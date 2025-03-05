from django.urls import path
from .views import chat_view, chat_api, new_chat, chat_history, chat_sessions, delete_chat

urlpatterns = [
    path("", chat_view, name="chat"),
    path("api/chat/", chat_api, name="chat_api"),  # ✅ LLM API 엔드포인트
    path("api/chat/new/", new_chat, name="new_chat"),  # ✅ 새로운 채팅 시작
    path("api/chat/sessions/", chat_sessions, name="chat_sessions"),  # ✅ 채팅 세션 목록 불러오기
    path("api/chat/<str:session_id>/", chat_history, name="chat_history"),  # ✅ 특정 채팅 내역 조회
    path("api/chat/delete/<str:session_id>/", delete_chat, name="delete_chat"),  # ✅ 특정 채팅 삭제
]
