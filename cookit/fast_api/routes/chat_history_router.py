# chat_history router
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from asgiref.sync import sync_to_async
from chat.models import ChatSession, HistoryChat

router = APIRouter()

@router.get("/history/{session_id}")
async def chat_history(session_id: str):
    """특정 세션의 채팅 내역을 불러옴 (login_required)"""
    try:
        # Django ORM 비동기 처리
        chat_session = await sync_to_async(ChatSession.objects.get)(session_id=session_id)
    except ChatSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다.")

    # HistoryChat 가져오기 (비동기)
    history = await sync_to_async(lambda: HistoryChat.objects.filter(session=chat_session).first())()
    if not history:
        return JSONResponse({"session_id": session_id, "messages": []})

    try:
        # Django ORM에서 가져온 JSON 데이터를 FastAPI의 dict 형태로 변환
        messages = json.loads(history.messages)
    except json.JSONDecodeError:
        messages = []

    message_list = [{"content": msg["content"], "sender": "User" if msg["role"] == "human" else "AI"} for msg in messages]

    # FastAPI에서 JSON 응답 반환
    return JSONResponse({"session_id": session_id, "messages": message_list})
