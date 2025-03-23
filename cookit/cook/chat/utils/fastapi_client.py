import requests
from dotenv import dotenv_values

FASTAPI_BASE_URL = dotenv_values()["FASTAPI_BASE_URL"]

def call_fastapi_chat(message, user_id=None, history_id=None, chat_history=[]):
    """FastAPI에 회원/비회원 채팅 요청 보내기"""
    url = f"{FASTAPI_BASE_URL}/chat/member_chat/" if user_id else f"{FASTAPI_BASE_URL}/chat/guest_chat/"
    payload = {
        "message": message,
        "user_id": user_id,
        "history_id": history_id,
        "chat_history": chat_history
    }
    response = requests.post(url, json=payload, timeout=10)
    return response.json() if response.status_code == 200 else {"error": "FastAPI 연결 실패"}

def call_fastapi_stt(audio_file):
    """FastAPI에 STT 요청 보내기"""
    url = f"{FASTAPI_BASE_URL}/speech/stt/"
    response = requests.post(url, files={"audio": audio_file})
    return response.json() if response.status_code == 200 else {"error": "STT 변환 실패"}

def call_fastapi_tts(text, user_id="default_user"):
    """FastAPI에 TTS 요청 보내기"""
    url = f"{FASTAPI_BASE_URL}/speech/tts/"
    payload = {"text": text, "user_id": user_id}
    response = requests.post(url, json=payload, timeout=10)
    return response.json() if response.status_code == 200 else {"error": "TTS 변환 실패"}

def call_fastapi_image_detect(images):
    """FastAPI에 이미지 업로드 요청 보내기 (Object Detection)"""
    url = f"{FASTAPI_BASE_URL}/image/detect/"
    files = [("images", (img.name, img.read(), img.content_type)) for img in images]
    response = requests.post(url, files=files)
    return response.json() if response.status_code == 200 else {"error": "이미지 감지 실패"}