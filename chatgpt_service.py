# chatgpt_service.py

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QBuffer, QIODevice
import requests
import base64
import os
from PyQt5.QtGui import QPixmap, QImage

class ChatGPTService(QObject):
    responseReady = pyqtSignal(str)    
    textToVoiceReady = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()     
        
    @pyqtSlot(str)
    def textToVoice(self, text: str):
        """
        將文本轉換為語音，並返回語音數據。
        """
        base_url = "free.gpt.ge"
        api_key = os.getenv('FREE_GPT_API_KEY')

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "tts-1",  # 使用 TTS 模型
                "input": text,
                "voice": "nova",  # 可以選擇不同的聲音，如 echo, fable, onyx, nova, shimmer
                "response_format": "mp3",  # 選擇音頻格式
                "speed": 1.0  # 可以調整語速，默認為 1.0
            }

            response = requests.post(f"https://{base_url}/v1/audio/speech", headers=headers, json=payload)

            if response.status_code == 200:
                audio_content = response.content
                self.textToVoiceReady.emit(audio_content)
            else:
                print(f"Error: {response.status_code}, {response.text}")
                self.textToVoiceReady.emit(b"")
        except Exception as e:
            print(f"發送文字轉語音過程中發生錯誤：{e}")
            self.textToVoiceReady.emit(b"")   

    @pyqtSlot(QPixmap)
    def sendImage(self, pixmap: QPixmap):
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

            prompt = "What’s in this image? use traditional chinese response."
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
