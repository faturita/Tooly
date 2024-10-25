from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from llama import Llama, Dialog
import multiprocessing
from typing import List, Optional
app = FastAPI()

class TollyHelloRequest(BaseModel):
    ckpt_dir: str = "llama-2-7b-chat/"
    tokenizer_path: str = "tokenizer.model"
    temperature: float = 0.6
    top_p: float = 0.9
    max_seq_len: int = 1024
    max_batch_size: int = 10
    max_gen_len: int = None

class Message(BaseModel):
    content: str

class ToolyConversationRequest(BaseModel):
    conversation_id: str
    message: Message

conversations = {}

def truncate_text(text, max_len):
    if len(text) > max_len:
        text = text[:max_len]
    return text

def generate_response(generator, dialogs):
    results = generator.chat_completion(dialogs)
    return truncate_text(results[0]['generation']['content'], 1024)

def worker(conversation_id, conversation, message_content, response_queue):
    # Inicializar PyTorch en el proceso secundario
    #conversation = conversations.get(conversation_id)
    print(conversation)
    if conversation:
        if conversation["generator"] is None:
            # Inicializar el generador con los parámetros de la solicitud
            conversation["generator"] = Llama.build(
                ckpt_dir=conversation["ckpt_dir"],
                tokenizer_path=conversation["tokenizer_path"],
                max_seq_len=conversation["max_seq_len"],
                max_batch_size=conversation["max_batch_size"],
            )
        elapsed_time = timedelta(minutes=30)
        if datetime.now() - conversation["start_time"] > elapsed_time:
            response = {"conversation_id": conversation_id, "response": "Conversation timeout"}
        else:
            conversation["start_time"] = datetime.now()
            generator = conversation["generator"]
            user_message = truncate_text(message_content, conversation["max_seq_len"])
            if conversation["dialogs"] is None:
                  dialogs: List[Dialog] = [
                        [{"role": "user", "content": user_message}],
                    ]
            else:
                dialogs = conversation["dialogs"] 
                dialogs[0].append({"role": "user", "content": user_message})
            
            
            
            response_content = generate_response(generator, dialogs)
            dialogs[0].append({"role": "assistant", "content": response_content})
            print(user_message)
            print(response_content)
            if len(dialogs[0]) >= conversation["max_batch_size"]:
                dialogs[0] = dialogs[0][-3:]
                conversation["dialogs"] = dialogs
            response = {"conversation_id": conversation_id, "response": response_content}
        response_queue.put(response)
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.post("/tooly_hello/")
def tooly_hello(request: TollyHelloRequest):
    # prompt = "Hello! How can I assist you?"
    # dialogs = [
    #     [{"role": "user", "content": prompt}],
    # ]
    conversation_id = str(datetime.now())
    conversations[conversation_id] = {
        "generator": None,  # Se inicializará en el proceso secundario
        "ckpt_dir": request.ckpt_dir,
        "tokenizer_path": request.tokenizer_path,
        "dialogs": None,
        "max_seq_len": request.max_seq_len,
        "start_time": datetime.now(),
        "max_batch_size": request.max_batch_size,
    }
    return {"conversation_id": conversation_id}

def worker_response(conversation_id, conversation, message_content):
    print("worker_response")
    response_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=worker, args=(conversation_id, conversation, message_content, response_queue))
    print(process)
    process.start()
    process.join()
    response = response_queue.get()
    return response

@app.post("/tooly/")
def tooly(request: ToolyConversationRequest):
    conversation = conversations.get(request.conversation_id)
    if conversation:
        response = worker_response(request.conversation_id, conversation, request.message.content)
        print(response)
        return response
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
