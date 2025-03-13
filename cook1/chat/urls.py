from django.urls import path
from .views import chat_api, chat_view, new_chat

urlpatterns = [
    path("", chat_view, name="chat"),  # 채팅 화면
    path("chat_api/", chat_api, name="chat_api"),  # LLM API 엔드포인트
    path("new_chat/", new_chat, name="new_chat"),  # 새로운 채팅 시작
]
