# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

from typing import List, Optional

import fire #script into terminal

from llama import Llama, Dialog

def truncate_text(text, max_len):
    if len(text) > max_len:
        text = text[:max_len]
    return text

def main(
    ckpt_dir: str,
    tokenizer_path: str,
    temperature: float = 0.6,
    top_p: float = 0.9,
    max_seq_len: int = 512,
    max_batch_size: int = 8,
    max_gen_len: Optional[int] = None,
):
    """
    Entry point of the program for generating text using a pretrained model.

    Args:
        ckpt_dir (str): The directory containing checkpoint files for the pretrained model.
        tokenizer_path (str): The path to the tokenizer model used for text encoding/decoding.
        temperature (float, optional): The temperature value for controlling randomness in generation.
            Defaults to 0.6.
        top_p (float, optional): The top-p sampling parameter for controlling diversity in generation.
            Defaults to 0.9.
        max_seq_len (int, optional): The maximum sequence length for input prompts. Defaults to 512.
        max_batch_size (int, optional): The maximum batch size for generating sequences. Defaults to 8.
        max_gen_len (int, optional): The maximum length of generated sequences. If None, it will be
            set to the model's max sequence length. Defaults to None.
    """
    generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
    )
    prompt = input("Tooly: Hello! how can i assist you?\n")
    dialogs: List[Dialog] = [
        [{"role": "user", "content": prompt}],
    ]

    while True:
        results = generator.chat_completion(
            dialogs,  # type: ignore
            max_gen_len=max_gen_len,
            temperature=temperature,
            top_p=top_p,
        )
        response = results[0]['generation']
        
        response_content = truncate_text(response['content'], max_seq_len)
        #print("chat: " + len(response_content))
        dialogs[0].append({
            "role": "assistant",
            "content": response_content,
        })
        
        prompt = input(f"You: {response['content']}\n")
        content_truncate = truncate_text(prompt, max_seq_len)
        #print("user: " + len(content_truncate))
        dialogs[0].append({
            "role": "user",
            "content": content_truncate
        })
        
        if len(dialogs[0]) >= max_batch_size:
            dialogs[0] = dialogs[0][-3:]
        

if __name__ == "__main__":
    fire.Fire(main)


# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional
# from datetime import datetime, timedelta

# from llama import Llama, Dialog
# app = FastAPI()

# class TollyHelloRequest(BaseModel):
#     ckpt_dir: str
#     tokenizer_path: str
#     temperature: float = 0.6
#     top_p: float = 0.9
#     max_seq_len: int = 512
#     max_batch_size: int = 8
#     max_gen_len: Optional[int] = None

# class Message(BaseModel):
#     content: str

# class ToolyConversationRequest(BaseModel):
#     conversation_id: str
#     message: Message
#     #elapsed_time: int  # elapsed time in seconds

# conversations = {}

# def truncate_text(text, max_len):
#     if len(text) > max_len:
#         text = text[:max_len]
#     return text

# def generate_response(generator, dialogs, max_gen_len, temperature, top_p):
#     results = generator.chat_completion(
#         dialogs,
#         max_gen_len=max_gen_len,
#         temperature=temperature,
#         top_p=top_p,
#     )
#     return truncate_text(results[0]['generation']['content'], max_gen_len)

# @app.post("/tooly_hello/")
# def tooly_hello(request: TollyHelloRequest):
#     generator = Llama.build(
#         ckpt_dir=request.ckpt_dir,
#         tokenizer_path=request.tokenizer_path,
#         max_seq_len=request.max_seq_len,
#         max_batch_size=request.max_batch_size,
#     )
#     prompt = input("Tooly: Hello! How can I assist you?\n")
#     dialogs = [
#         [{"role": "user", "content": prompt}],
#     ]
#     conversation_id = str(datetime.now())
#     conversations[conversation_id] = {
#         "generator": generator,
#         "dialogs": dialogs,
#         "start_time": datetime.now(),
#     }
#     return {"conversation_id": conversation_id}

# @app.post("/tooly/")
# def tooly(request: ToolyConversationRequest):
#     conversation = conversations.get(request.conversation_id)
#     if not conversation:
#         raise HTTPException(status_code=404, detail="Conversation not found")

#     #lapsed_time = timedelta(seconds=request.elapsed_time)
#     elapsed_time = timedelta(minutes=10) 
#     if datetime.now() - conversation["start_time"] > elapsed_time:
#         return {"response": "Conversation timeout"}

#     generator = conversation["generator"]
#     dialogs = conversation["dialogs"]
#     response_content = generate_response(
#         generator,
#         dialogs,
#         request.max_gen_len,
#         request.temperature,
#         request.top_p,
#     )

#     user_message = truncate_text(request.message.content, request.max_seq_len)
#     dialogs[0].append({"role": "user", "content": user_message})

#     dialogs[0].append({"role": "assistant", "content": response_content})

#     if len(dialogs[0]) >= request.max_batch_size:
#         dialogs[0] = dialogs[0][-3:]

#     return {"response": response_content}

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="127.0.0.1", port=8000)


# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# import json
# from llama import Llama, Dialog
# import asyncio
# from multiprocessing import Process

# app = FastAPI()

# class TollyHelloRequest(BaseModel):
#     ckpt_dir: str
#     tokenizer_path: str
#     temperature: float = 0.6
#     top_p: float = 0.9
#     max_seq_len: int = 512
#     max_batch_size: int = 8
#     max_gen_len: int = None

# class Message(BaseModel):
#     content: str

# class ToolyConversationRequest(BaseModel):
#     conversation_id: str
#     message: Message

# conversations = {}

# def truncate_text(text, max_len):
#     if len(text) > max_len:
#         text = text[:max_len]
#     return text

# def generate_response(generator, dialogs):
#     results = generator.chat_completion(
#         dialogs,
#     )
#     return truncate_text(results[0]['generation']['content'])

# def worker(conversation_id, message_content, response_queue):
#     # Inicializar PyTorch en el proceso secundario
#     conversation = conversations.get(conversation_id)
#     if conversation:
#         if conversation["generator"] is None:
#             # Inicializar el generador con los parámetros de la solicitud
#             conversation["generator"] = Llama.build(
#                 ckpt_dir=conversation["ckpt_dir"],
#                 tokenizer_path=conversation["tokenizer_path"],
#                 max_seq_len=conversation["max_seq_len"],
#                 max_batch_size=conversation["max_batch_size"],
#             )
#         elapsed_time = timedelta(minutes=10)
#         if datetime.now() - conversation["start_time"] > elapsed_time:
#             response = {"conversation_id": conversation_id, "response": "Conversation timeout"}
#         else:
#             generator = conversation["generator"]
#             dialogs = conversation["dialogs"]
#             response_content = generate_response(
#                 generator,
#                 dialogs,
#             )
#             user_message = truncate_text(message_content)
#             dialogs[0].append({"role": "user", "content": user_message})
#             dialogs[0].append({"role": "assistant", "content": response_content})
#             print(user_message)
#             print(response_content)
#             if len(dialogs[0]) >= conversation["max_batch_size"]:
#                 dialogs[0] = dialogs[0][-3:]
#             response = {"conversation_id": conversation_id, "response": response_content}
#         response_queue.put(response)

# @app.post("/tooly_hello/")
# def tooly_hello(request: TollyHelloRequest):
#     prompt = "Hello! How can I assist you?"
#     dialogs = [
#         [{"role": "user", "content": prompt}],
#     ]
#     conversation_id = str(datetime.now())
#     conversations[conversation_id] = {
#         "generator": None,  # Se inicializará en el proceso secundario
#         "dialogs": dialogs,
#         "start_time": datetime.now(),
#         "max_batch_size": request.max_batch_size,
#     }
#     return {"conversation_id": conversation_id}

# async def worker_response(conversation_id, message_content):
#     loop = asyncio.get_event_loop()
#     response_queue = asyncio.Queue()

#     process = Process(target=worker, args=(conversation_id, message_content,  response_queue))
#     process.start()

#     while True:
#         try:
#             response = await loop.run_in_executor(None, response_queue.get)
#             return response
#         except asyncio.CancelledError:
#             process.terminate()
#             raise
#         finally:
#             process.join()

# @app.post("/tooly/")
# async def tooly(request: ToolyConversationRequest):
#     conversation = conversations.get(request.conversation_id)
#     if conversation:
#         response = await worker_response(request.conversation_id, request.message.content)
#         print(response)
#         return response
#     else:
#         raise HTTPException(status_code=404, detail="Conversation not found")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)


#########################
    
#     from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# from llama import Llama, Dialog
# import multiprocessing

# app = FastAPI()

# class TollyHelloRequest(BaseModel):
#     ckpt_dir: str = "llama-2-7b-chat/"
#     tokenizer_path: str = "tokenizer.model"
#     temperature: float = 0.6
#     top_p: float = 0.9
#     max_seq_len: int = 512
#     max_batch_size: int = 8
#     max_gen_len: int = None

# class Message(BaseModel):
#     content: str

# class ToolyConversationRequest(BaseModel):
#     conversation_id: str
#     message: Message

# conversations = {}

# def truncate_text(text, max_len):
#     if len(text) > max_len:
#         text = text[:max_len]
#     return text

# def generate_response(generator, dialogs):
#     results = generator.chat_completion(dialogs)
#     return truncate_text(results[0]['generation']['content'], 512)

# def worker(conversation_id, conversation, message_content, response_queue):
#     print("HOLA")
#     # Inicializar PyTorch en el proceso secundario
#     #conversation = conversations.get(conversation_id)
#     print(conversation)
#     if conversation:
#         if conversation["generator"] is None:
#             # Inicializar el generador con los parámetros de la solicitud
#             conversation["generator"] = Llama.build(
#                 ckpt_dir=conversation["ckpt_dir"],
#                 tokenizer_path=conversation["tokenizer_path"],
#                 max_seq_len=conversation["max_seq_len"],
#                 max_batch_size=conversation["max_batch_size"],
#             )
#         elapsed_time = timedelta(minutes=10)
#         if datetime.now() - conversation["start_time"] > elapsed_time:
#             response = {"conversation_id": conversation_id, "response": "Conversation timeout"}
#         else:
#             print("adentro")
#             generator = conversation["generator"]
#             dialogs = conversation["dialogs"]
#             print(dialogs)
#             print(generator)
#             response_content = generate_response(generator, dialogs)
#             print(response_content)
#             user_message = truncate_text(message_content, conversation["max_seq_len"])
#             dialogs[0].append({"role": "user", "content": user_message})
#             dialogs[0].append({"role": "assistant", "content": response_content})
#             print(user_message)
#             print(response_content)
#             if len(dialogs[0]) >= conversation["max_batch_size"]:
#                 dialogs[0] = dialogs[0][-3:]
#             response = {"conversation_id": conversation_id, "response": response_content}
#         response_queue.put(response)
#     else:
#         raise HTTPException(status_code=404, detail="Conversation not found")

# @app.post("/tooly_hello/")
# def tooly_hello(request: TollyHelloRequest):
#     prompt = "Hello! How can I assist you?"
#     dialogs = [
#         [{"role": "user", "content": prompt}],
#     ]
#     conversation_id = str(datetime.now())
#     conversations[conversation_id] = {
#         "generator": None,  # Se inicializará en el proceso secundario
#         "ckpt_dir": request.ckpt_dir,
#         "tokenizer_path": request.tokenizer_path,
#         "max_seq_len": request.max_seq_len,
#         "dialogs": dialogs,
#         "start_time": datetime.now(),
#         "max_batch_size": request.max_batch_size,
#     }
#     return {"conversation_id": conversation_id}

# def worker_response(conversation_id, conversation, message_content):
#     print("worker_response")
#     response_queue = multiprocessing.Queue()
#     process = multiprocessing.Process(target=worker, args=(conversation_id, conversation, message_content, response_queue))
#     print(process)
#     process.start()
#     process.join()
#     response = response_queue.get()
#     return response

# @app.post("/tooly/")
# def tooly(request: ToolyConversationRequest):
#     conversation = conversations.get(request.conversation_id)
#     if conversation:
#         response = worker_response(request.conversation_id, conversation, request.message.content)
#         print(response)
#         return response
#     else:
#         raise HTTPException(status_code=404, detail="Conversation not found")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)
