# new_chat router
import json
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from chat.models import ChatSession, HistoryChat

router = APIRouter()

@router.post("/new_chat/")
async def new_chat(request: Request):
    """새로운 채팅을 생성하고 ID 반환 (login_required)"""
    try:
        # Django에서 전달한 JSON 데이터 받기
        data = await request.json()
        user_id = data.get("user_id")

        if not user_id:
            return JSONResponse({"success": False, "error": "user_id가 필요합니다."}, status=400)

        chat_session = await sync_to_async(ChatSession.objects.create)(user_id=user_id)
        history = await sync_to_async(HistoryChat.objects.create)(user_id=user_id, session=chat_session, title="새로운 대화", messages=json.dumps([]))
        return JSONResponse({"success": True, "chat_id": str(chat_session.session_id), "title": history.title})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
