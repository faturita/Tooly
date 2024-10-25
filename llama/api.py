from llama import Llama
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import torch.distributed as dist
import argparse
import os
import json
from pydantic import BaseModel
from typing import List

app = FastAPI()

parser = argparse.ArgumentParser(description="Llama 2 FastAPI")

parser.add_argument('--model', type=str, default='7b-chat', help='The model name (str)')
parser.add_argument('--max_seq_len', type=int, default=512, help='Maximum sequence length (int)')
parser.add_argument('--backend', type=str, default='nccl', help='Backend (nccl for GPU, gloo for CPU) (str)')
parser.add_argument('--temperature', type=float, default=0.6, help='Temperature for sampling (float)')
parser.add_argument('--top_p', type=float, default=0.9, help='Top p value for nucleus sampling (float)')
parser.add_argument('--world_size', type=int, default=None, help='Number of parallel processes (int)')
parser.add_argument('--max_batch_size', type=int, default=4, help='Maximum batch size (int)')
parser.add_argument('--max_gen_len', type=int, default=None, help='Maximum generation length (int)')
parser.add_argument('--tokenizer_path', type=str, default='tokenizer.model', help='Path to tokenizer model (str)')
parser.add_argument('--ckpt_dir', type=str, default=None, help='The full path to the model directory (str)')
parser.add_argument('--llama_addr', type=str, default='127.0.0.1', help='Llama 2 master address (str)')
parser.add_argument('--llama_port', type=int, default=29500, help='Llama 2 master port (int)')
args = parser.parse_args()

# get default ckpt_dir if not provided
if args.ckpt_dir is None:
    args.ckpt_dir = "llama-2-" + args.model

# guess world size if not provided
if args.world_size is None:
    if "7b" in args.ckpt_dir.lower():
        args.world_size = 1
    elif "13b" in args.ckpt_dir.lower():
        args.world_size = 2
    elif "70b" in args.ckpt_dir.lower():
        args.world_size = 8

notices = False

# check checkpoint dir location
if not os.path.exists(args.ckpt_dir):
    parent_ckpt_dir = os.path.join("..", args.ckpt_dir)
    if os.path.exists(parent_ckpt_dir):
        print(f"NOTICE: Reading model from '{parent_ckpt_dir}'")
        args.ckpt_dir = parent_ckpt_dir
    else:
        print(f"WARNING: Model directory '{args.ckpt_dir}' not found!")
    notices = True

# check tokenizer location
if not os.path.exists(args.tokenizer_path):
    parent_tokenizer_path = os.path.join("..", args.tokenizer_path)
    if os.path exists(parent_tokenizer_path):
        print(f"NOTICE: Reading tokenizer from '{parent_tokenizer_path}'")
        args.tokenizer_path = parent_tokenizer_path
    else:
        print(f"WARNING: Tokenizer file '{args.tokenizer_path}' not found!")
    notices = True

if notices:
    print()

# initialize queues
request_queues = [Queue() for _ in range(args.world_size)]
response_queues = [Queue() for _ in range(args.world_size)]

class Message(BaseModel):
    role: str
    content: str

def respond_json(response, key="message"):
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "choices": [{
            "index": 0,
            key: response,
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

@app.post("/chat")
def message_route(messages: List[Message], stream: bool = False):
    # validate message format
    for message in messages:
        if message.role not in ["system", "user", "assistant"]:
            raise HTTPException(status_code=400, detail="Invalid 'role' in message.")
    if len(messages) < 1:
        raise HTTPException(status_code=400, detail="At least one message is required in 'messages' list.")

    # add messages to queue for Llama 2
    for rank in range(args.world_size):
        request_queues[rank].put(messages)

    # wait for response
    for rank in range(args.world_size):
        response = response_queues[rank].get()

    if stream:
        def generate():
            maxlen = 128
            rc = response["content"]
            deltas = [rc[i:i+maxlen] for i in range(0, len(rc), maxlen)]
            for delta in deltas:
                delta_response = {
                    "role": response["role"],
                    "content": delta
                }
                yield json.dumps(respond_json(delta_response, "delta")) + "\n"
            yield "[DONE]"

        return StreamingResponse(generate(), media_type="text/event-stream")

    return respond_json(response)

if __name__ == "__main__":
    print("Initializing Llama 2...")
    print(f"Model: {args.ckpt_dir}\n")

    processes = []

    # initialize all Llama 2 processes
    for rank in range(args.world_size):
        p = Process(target=init_process, args=(rank, args.world_size, run, request_queues[rank], response_queues[rank]))
        p.start()
        processes.append(p)

    # wait for Llama 2 initialization
    for rank in range(args.world_size):
        response = response_queues[rank].get()

    print("\nStarting FastAPI...")

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)