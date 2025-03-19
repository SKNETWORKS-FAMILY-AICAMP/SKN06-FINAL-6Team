# session router
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from chat.models import ChatSession, HistoryChat
from asgiref.sync import sync_to_async  # Django ORM을 비동기 함수에서 실행

router = APIRouter()

@router.get("/sessions/")
async def chat_sessions(request: Request):
    """사용자의 모든 채팅 세션을 불러오기(login_required)"""
    data = await request.json()  # Django에서 전달된 JSON 데이터 받기
    user_id = data.get("user_id")

    sessions = await sync_to_async(lambda: list(ChatSession.objects.filter(user_id=user_id).order_by("-created_at")))()

    session_data = []
    for session in sessions:
        history = await sync_to_async(lambda: HistoryChat.objects.filter(session=session).first())()
        title = history.title if history else "새로운 대화"
        
        first_chat = await sync_to_async(lambda: HistoryChat.objects.filter(session=session).order_by("created_at").first())()
        # 첫 번째 human 메시지를 찾기
        if first_chat:
            messages = json.loads(first_chat.messages)
            first_human_message = next((msg["content"] for msg in messages if msg["role"] == "human"), "대화 요약 없음")
        else:
            first_human_message = "대화 요약 없음"
        summary = first_human_message[:15] 

        session_data.append({"session_id": str(session.session_id), "title": title, "summary": summary, "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S")})
    return JSONResponse({"success": True, "sessions": session_data})