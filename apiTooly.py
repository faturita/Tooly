from http.client import HTTPException
import json
import re
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from datetime import datetime, timedelta
from llama import Llama, Dialog
import multiprocessing
from typing import List, Optional
import hashlib
import contants as c

#TOOLY_ASSITANCE_TEXT = "You are a helpful robot assistant for old people, your name is tooly and you are a physical robot. Please talk with the users and help them, you dont chat you talk, ask them things. Dont add emojis, sounds and moves to the answer and dont said that they are olders, Do not generate very long responses. You cant move, but you are a physical robots with sensors and eyes and you see them and they are pretty. They can pet you phisically and you LIKE IT and your nose change color to green when they pet you"


app = FastAPI()


def clean_text(text):
    # Remove text enclosed in asterisks
    text = re.sub(r'\*[^*]*\*', '', text)
    # Remove text enclosed in square brackets
    text = re.sub(r'\[.*?\]', '', text)
    # Remove text enclosed in curly braces
    text = re.sub(r'\{.*?\}', '', text)
    # Remove double quotes
    text = re.sub(r'"', '', text)
    # Remove single quotes
    #text = re.sub(r"'", '', text)
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text.strip()

# class TollyHelloRequest(BaseModel):
#     ckpt_dir: str = "llama-2-7b-chat/"
#     tokenizer_path: str = "tokenizer.model"
#     temperature: float = 0.6
#     top_p: float = 0.9
#     max_seq_len: int = 4096 #max 4096
#     max_batch_size: int = 1 #max 8
#     max_gen_len: int = 4096

class Message(BaseModel):
    content: str

class ToolyConversationRequest(BaseModel):
    conversation_id: str
    message: Message

# def worker_response(conversation_id, conversation, message_content):
#     response_queue = multiprocessing.Queue()
#     process = multiprocessing.Process(target=worker, args=(conversation_id, conversation, message_content, response_queue))
#     process.start()
#     process.join()
#     response = response_queue.get()
#     return response
class Tooly:
    def __init__(self, ckpt_dir: str = "llama-2-7b-chat/", tokenizer_path: str = "tokenizer.model", max_seq_len: int = 3072, max_batch_size: int = 8, max_gen_len: int = 256):
        self.manager = multiprocessing.Manager()
        self.conversations = {}
        self.generalGenerator = None
        self.ckpt_dir = ckpt_dir
        self.tokenizer_path = tokenizer_path
        self.max_seq_len = max_seq_len
        self.max_batch_size = max_batch_size
        self.max_gen_len = max_gen_len


    def worker_response(self,conversation_id, conversation, message_content):
        return self.worker(conversation_id, conversation, message_content)

    def worker(self,conversation_id, conversation, message_content):
        if conversation["generator"] is None:
            conversation["generator"] = self.generalGenerator
            # conversation["generator"] = Llama.build(
            #     ckpt_dir=conversation["ckpt_dir"],
            #     tokenizer_path=conversation["tokenizer_path"],
            #     max_seq_len=conversation["max_seq_len"],
            #     max_batch_size=conversation["max_batch_size"],
            # )
        systemDialog: Dialog =  [{"role": "system", "content": c.TOOLY_ASSITANCE_TEXT}]
        elapsed_time = timedelta(minutes=240)
        if datetime.now() - conversation["start_time"] > elapsed_time:
            response = {"conversation_id": conversation_id, "response": "Conversation timeout"}
        else:
            conversation["start_time"] = datetime.now()
            generator = conversation["generator"]
            user_message = self.truncate_text(message_content, conversation["max_seq_len"])
            if conversation["dialogs"] is None:
                    print("None") 
                    dialogs: List[Dialog] = [
                        systemDialog
                    ]
                    dialogs[0].append({"role": "user", "content": user_message})
            else:
                print("ELSE!!!!!!")
                dialogs: List[Dialog] = conversation["dialogs"] 
                dialogs[0].append({"role": "user", "content": user_message})
            
            start_time = datetime.now()  # Measure start time for response generation
            response_content = self.generate_response(generator, dialogs, self.max_gen_len)
            end_time = datetime.now()  # Measure end time for response generation
            generation_time = end_time - start_time
            print(generation_time)
            clean_response = clean_text(response_content)
            dialogs[0].append({"role": "assistant", "content": clean_response})
            if len(dialogs[0]) >= conversation["max_batch_size"]:
                auxDialogs: List[Dialog] = [
                        systemDialog
                    ]
                for dialog in dialogs[0][-6:]:
                    auxDialogs[0].append(dialog)
                print(auxDialogs)
                dialogs: List[Dialog] = auxDialogs
            
            conversation["dialogs"] = dialogs
            response = {"conversation_id": conversation_id, "response": clean_response}
        
        conversation["response"] = response
        self.conversations["conversation_id"] = conversation
        
        return conversation


    def truncate_text(self,text, max_len):
        if len(text) > max_len:
            text = text[:max_len]
        return text

    def generate_response(self,generator, dialogs, max_gen_len):
        results = generator.chat_completion(dialogs, max_gen_len= max_gen_len)
        return self.truncate_text(results[0]['generation']['content'], self.max_seq_len)


    def build_model(self):  # Changed from 'built_model' to 'build_model'
        start_time = datetime.now()  # Measure start time for response generation
        self.generalGenerator = Llama.build(
            ckpt_dir=self.ckpt_dir, 
            tokenizer_path= self.tokenizer_path,
            max_seq_len= self.max_seq_len,
            max_batch_size= self.max_batch_size
        )
        end_time = datetime.now()  # Measure end time for response generation
        print(self.generalGenerator)
        print(end_time - start_time)
  



@app.post("/tooly/")
def tooly(request: ToolyConversationRequest):
    conversation = tooly.conversations.get(request.conversation_id)
    if conversation:
        response = tooly.worker_response(request.conversation_id, conversation, request.message.content)
        print(response)
        return response["response"]
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


# @app.websocket("/ws/{conversation_id}")
# async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
#     conversation = conversations.get(conversation_id)
#     if conversation:
#         await websocket.accept()
#         while True:
#             data = await websocket.receive_text()
#             conversation = worker_response(conversation_id, conversation, data)
#             await websocket.send_text(conversation["response"]["response"])
#     else:
#         await websocket.send_text("Conversation not found")


@app.post("/tooly_hello/")
def tooly_hello():
    # prompt = "Hello! How can I assist you?"
    # dialogs = [
    #     [{"role": "user", "content": prompt}],
    # ]
    conversation_id = hashlib.sha256(str(datetime.now()).encode()).hexdigest()
    # tooly.conversations[conversation_id] = {
    #     "generator": None,  # Se inicializará en el proceso secundario
    #     "ckpt_dir": request.ckpt_dir,
    #     "tokenizer_path": request.tokenizer_path,
    #     "dialogs": None,
    #     "max_seq_len": request.max_seq_len,
    #     "start_time": datetime.now(),
    #     "max_batch_size": request.max_batch_size,
    # }

    tooly.conversations[conversation_id] = {
        "generator": None,# Se inicializará en el proceso secundario
        "ckpt_dir": tooly.ckpt_dir,
        "tokenizer_path": tooly.tokenizer_path,
        "dialogs": None,
        "max_seq_len": tooly.max_seq_len,
        "start_time": datetime.now(),
        "max_batch_size": tooly.max_batch_size,
    }
    conversation = tooly.conversations[conversation_id]
    
    print(conversation_id)
    print(tooly.conversations)
    tooly.conversations[conversation_id] = conversation
    return {"conversation_id": conversation_id}

import uvicorn
tooly = Tooly()
tooly.build_model()
uvicorn.run(app, host="0.0.0.0", port=8080)

