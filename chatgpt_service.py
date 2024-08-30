# chatgpt_service.py

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QBuffer, QIODevice
import requests
import base64
import os
from PyQt5.QtGui import QPixmap, QImage
import torch
import ChatTTS
import numpy

class ChatGPTService(QObject):
    responseReady = pyqtSignal(str)    
    textToVoiceReady = pyqtSignal(numpy.ndarray)

    def __init__(self):
        super().__init__()     
        self.chat = ChatTTS.Chat()
        self.chat.load()
        self.textToVoice("您好")
        
    @pyqtSlot(str)
    def textToVoice(self, text: str):
        texts = [ text ]
        wavs = self.chat.infer(texts, use_decoder=True)
        self.textToVoiceReady.emit(wavs[0])
    
    @pyqtSlot(QPixmap, str)
    def sendImage(self, pixmap: QPixmap, prompt: str):
        """
        將 QPixmap 圖片轉換為 base64 並以文本形式發送到 OpenAI API 進行分析。
        """
        base_url = "free.gpt.ge"
        api_key = os.getenv('FREE_GPT_API_KEY')

        try:
            image = pixmap.toImage()
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            byte_data = buffer.data()
            encoded_image = base64.b64encode(byte_data).decode('utf-8')

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            #prompt = "What’s in this image? use traditional chinese response."
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                        ]
                    }
                ],
                "max_tokens": 300
            }

            response = requests.post(f"https://{base_url}/v1/chat/completions", headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    message_content = result['choices'][0]['message']['content']
                    self.responseReady.emit(message_content)
                else:
                    print("Unexpected response format:", result)
            else:
                print(f"Error: {response.status_code}, {response.text}")
                self.responseReady.emit("Error occurred while contacting the API.")
        except Exception as e:
            print(f"發送圖片過程中發生錯誤：{e}")
            self.responseReady.emit(f"發送圖片過程中發生錯誤：{e}")
