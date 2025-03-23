from django.urls import path
from chat.views import chat_api, chat_view, new_chat, chat_history, chat_sessions, delete_chat, stt_api, tts_api, update_retriever
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", chat_view, name="chat"),  # 채팅 화면
    path("chat/<str:session_id>/", chat_api, name="chat_api"),  # LLM API 엔드포인트
    path("new_chat/", new_chat, name="new_chat"),  # 새로운 채팅 시작
    path("sessions/", chat_sessions, name="chat_sessions"),  # 채팅 세션 목록 불러오기
    path("history/<str:session_id>/", chat_history, name="chat_history"),  # 특정 채팅 내역 조회
    path("delete/<str:session_id>/", delete_chat, name="delete_chat"),  
    path("speech/stt/", stt_api, name="stt_api"),
    path("speech/tts/", tts_api, name="tts_api"),
    path("update_retriever/", update_retriever, name="update_retriever"), # 추가
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)