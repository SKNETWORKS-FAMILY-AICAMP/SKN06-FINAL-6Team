from django.urls import path
from .views import chat_view, chat_api, new_chat, chat_history, chat_sessions, delete_chat


urlpatterns = [
    path("", chat_view, name="chat"),
    path("api/chat/", chat_api, name="chat_api"),  # LLM API 엔드포인트 추가
    path("api/new_chat/", new_chat, name="new_chat"),
    path("api/chat/<str:session_id>/", chat_history, name="chat_history"),
    path("api/chat_sessions/", chat_sessions, name="chat_sessions"),
    path("api/delete_chat/<str:session_id>/", delete_chat, name="delete_chat"),
]