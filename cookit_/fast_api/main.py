import os
import sys
import django

# 현재 스크립트의 위치를 기준으로 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "cook"))

# Django 환경 로드
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cook.settings")
django.setup()

from fastapi import FastAPI
from routes.chat_router import router as chat_router
from routes.chat_sessions_router import router as chat_sessions_router
from routes.chat_history_router import router as chat_history_router
from routes.delete_chat_router import router as delete_chat_router
from routes.new_chat_router import router as new_chat_router
from routes.update_retriever_router import router as update_retriever_router

app = FastAPI()

# 라우터 등록
app.include_router(chat_router, prefix="/chat_api")
app.include_router(chat_sessions_router, prefix="/sessions")
app.include_router(chat_history_router, prefix="/history")
app.include_router(delete_chat_router, prefix="/delete")
app.include_router(new_chat_router, prefix="/new_chat")
app.include_router(update_retriever_router, prefix="/update")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)