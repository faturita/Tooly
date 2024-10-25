import requests

url = "http://pf-2023a-tooly.it.itba.edu.ar"
def Llama2Connect():
    data_requests = {
        "ckpt_dir": "llama-2-7b-chat",
        "tokenizer_path": "tokenizer.model"
    }
    url_hello = url+ "tooly_hello/"
    response = requests.post(url_hello,json=data_requests)
    if response.status_code == 200:
        conv_id = response.json()["conversationId"]
        return conv_id
    else:
        print(response)
            
def Llama2(conv_id, msg):
    url = url+ "tooly/"
    data_requests = {
        "conversation_id": conv_id,
        "message": {
                "content": msg
            }
    }
    response = requests.post(url,json=data_requests)
    print(response)

def main():
    id = Llama2Connect()
    Llama2(id,"hola")
