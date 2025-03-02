#!/usr/bin/env python2.7

# NOTE: this example requires PyAudio because it uses the Microphone class

# install TTs google
# sudo pip install gTTS 


import speech_recognition as sr
import subprocess
import pipes
import json
import apiai
import time
import yaml
import os
import wave
import requests
import websocket
import gevent
from gevent import monkey
# from gtts import gTTS

#url_requests = "http://pf-2023a-tooly.it.itba.edu.ar"
monkey.patch_all()
url = "http://pf-2023a-tooly.it.itba.edu.ar"
wsUrl = "ws://pf-2023a-tooly.it.itba.edu.ar/ws/"
class QBOtalk:
    def __init__(self):
	config = yaml.safe_load(open("/home/pi/Documents/config.yml"))
        # obtain audio from the microphone
        self.r = sr.Recognizer()
        self.Response = "hello"
        self.GetResponse = False
        self.GetAudio = False
        self.strAudio = ""
	self.config = config
        
        for i, mic_name in enumerate (sr.Microphone.list_microphone_names()):
            if(mic_name == "dmicQBO_sv"):
                self.m = sr.Microphone(i)
        with self.m as source:        
            self.r.adjust_for_ambient_noise(source)

    def Decode(self, audio):
        try:

	    if (self.config["language"] == "spanish"):
	        str = self.r.recognize_google(audio, language="es-ES")
            else:
                str = self.r.recognize_google(audio)
	    print "LISTEN: " + str
        except sr.UnknownValueError:
            str = ""
        except sr.RequestError as e:
            str = "Could not request results from Speech Recognition service"
        return str

    def downsampleWav(self, src):
	print "src: " + src
        s_read = wave.open(src, 'r')
	print "frameRate: " + s_read.getframerate()
	s_read.setframerate(16000)
	print "frameRate_2: " + s_read.getframerate()
	return


    def downsampleWave_2(self, src, dst, inrate, outrate, inchannels, outchannels):
        if not os.path.exists(src):
            print 'Source not found!'
            return False

        if not os.path.exists(os.path.dirname(dst)):
	    print "dst: " + dst
	    print "path: " + os.path.dirname(dst)
            os.makedirs(os.path.dirname(dst))

        try:
            s_read = wave.open(src, 'r')
            s_write = wave.open(dst, 'w')
        except:
            print 'Failed to open files!'
            return False

        n_frames = s_read.getnframes()
        data = s_read.readframes(n_frames)

        try:
            converted = audioop.ratecv(data, 2, inchannels, inrate, outrate, None)
            if outchannels == 1:
                converted = audioop.tomono(converted[0], 2, 1, 0)
        except:
            print 'Failed to downsample wav'
            return False

        try:
            s_write.setparams((outchannels, 2, outrate, 0, 'NONE', 'Uncompressed'))
            s_write.writeframes(converted)
        except:
            print 'Failed to write wav'
            return False

        try:
            s_read.close()
            s_write.close()
        except:
            print 'Failed to close wav files'
            return False

        return True

    def SpeechText(self, text_to_speech):
	self.config = yaml.safe_load(open("/home/pi/Documents/config.yml"))
	print "config:" + str(self.config)

        if (self.config["language"] == "spanish"):
            speak = "pico2wave -l \"es-ES\" -w /home/pi/Documents/pico2wave.wav \"<volume level='" + str(self.config["volume"]) + "'>" + text_to_speech + "\" && aplay -D convertQBO /home/pi/Documents/pico2wave.wav"
#               speak = "pico2wave -l \"es-ES\" -w /var/local/pico2wave.wav \"" + text_to_speech + "\" | aplay -D convertQBO"
        else:
            speak = "pico2wave -l \"en-US\" -w /home/pi/Documents/pico2wave.wav \"<volume level='" + str(self.config["volume"]) + "'>" + text_to_speech + "\" && aplay -D convertQBO /home/pi/Documents/pico2wave.wav"
#               speak = "pico2wave -l \"en-US\" -w /var/local/pico2wave.wav \"" + text_to_speech + "\" | aplay -D convertQBO"

#        speak = "espeak -ven+f3 \"" + text_to_speech + "\" --stdout  | aplay -D convertQBO"

#       tts = gTTS(text = text_to_speech, lang = 'en')
#       tts.save("/home/pi/Documents/say.wav")
#       self.downsampleWav("/home/pi/Documents/say.wav")
#       self.downsampleWav("./say.wav", "./say16.wav", 8000, 16000, 1, 1)
#       downsampleWav("say.wav", "say16.wav")
#       os.system("aplay -D convertQBO say16.wav")
# hasta aqui

        print "QBOtalk: " + speak.encode('utf-8')
        result = subprocess.call(speak, shell = True)
    

    def SpeechText_2(self, text_to_speech, text_spain):
	self.config = yaml.safe_load(open("/home/pi/Documents/config.yml"))
	print "config:" + str(self.config)
	if (self.config["language"] == "spanish"):
	    speak = "pico2wave -l \"es-ES\" -w /home/pi/Documents/pico2wave.wav \"<volume level='" + str(self.config["volume"]) + "'>" + text_spain + "\" && aplay -D convertQBO /home/pi/Documents/pico2wave.wav"
	else:
            speak = "pico2wave -l \"en-US\" -w /home/pi/Documents/pico2wave.wav \"<volume level='" + str(self.config["volume"]) + "'>" + text_to_speech + "\" && aplay -D convertQBO /home/pi/Documents/pico2wave.wav"

        print "QBOtalk_2: " + speak.encode('utf-8')
	result = subprocess.call(speak, shell = True)
    
    def callback(self, recognizer, audio):
        try:
            self.Response = self.Decode(audio)
            self.GetResponse = True
            print("Google say ")
            #self.SpeechText(self.Response)
        except:
            return
        
    def callback_listen(self, recognizer, audio):
        print("callback listen")
        try:
            #strSpanish = self.r.recognize_google(audio,language="es-ES")
#	    with open("microphone-results.wav", "wb") as f:
#    		f.write(audio.get_wav_data())
            if (self.config["language"] == "spanish"):
                self.strAudio = self.r.recognize_google(audio, language="es-ES")
            else:
                self.strAudio = self.r.recognize_google(audio)

            self.strAudio = self.r.recognize_google(audio)
	    self.GetAudio = True
            print("listen: " + self.strAudio)
            #print("listenSpanish: ", strSpanish)
            #self.SpeechText(self.Response)
        except:
            print("callback listen exception")
            self.strAudio = ""
            return


    def Llama2Connect(self):
        data_requests = {
            "ckpt_dir": "llama-2-7b-chat",
            "tokenizer_path": "tokenizer.model"
        }
        url_hello = url + "/tooly_hello/"
        response = requests.post(url_hello, json=data_requests)
        print(response.text)
        if response.status_code == 200:
            conv_id = response.json()["conversation_id"]
            return conv_id
        else:
            print(response)

    
    def Llama2(self, conv_id, msg):
        url_tooly = wsUrl+ conv_id
        data_requests = msg
        print(url_tooly)
        ws = websocket.create_connection(url_tooly)
        ws.send(data_requests)
        #ws.connect(url_tooly)
        
        response = ws.recv()
        #response = requests.post(url_tooly, json=data_requests)
        return response
        
    def Start(self, conv_id):
        print("Say something!")
        self.r.operation_timeout = 10
        with self.m as source:
            audio = self.r.listen(source = source, timeout = 10)

        # recognize speech using Google Speech Recognition

        Response = self.Decode(audio)
        llama2Response = self.wsLlama2(conv_id,Response)
        self.SpeechText(llama2Response)
        
    def StartBack(self):
        with self.m as source:
            self.r.adjust_for_ambient_noise(source)

        print("start background listening")

        return self.r.listen_in_background(self.m, self.callback)

    def StartBackListen(self):
        with self.m as source:
            self.r.adjust_for_ambient_noise(source)

        print("start background only listening")

        return self.r.listen_in_background(self.m, self.callback_listen)


gevent.monkey.patch_all()
qbo = QBOtalk()
conv_id = qbo.Llama2Connect()
while True:
    qbo.Start(conv_id)
    gevent.sleep(0.1)


