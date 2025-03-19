# delete_chat router
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from chat.models import ChatSession, HistoryChat
from asgiref.sync import sync_to_async  # Django ORM을 비동기 함수에서 실행

router = APIRouter()

@router.delete("/delete/{session_id}/")
async def delete_chat(request: Request, session_id: str):
    """특정 채팅 세션 삭제 (login_required)"""
    try:
        # Django에서 전달한 JSON 데이터 받기
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return JSONResponse({"success": False, "error": "user_id가 필요합니다."}, status=400)
        # 세션이 존재하는지 확인 (비동기 ORM 최적화)
        session_exists = await sync_to_async(ChatSession.objects.filter(session_id=session_id, user_id=user_id).exists)()
        if not session_exists:
            return JSONResponse({"success": False, "error": "세션이 존재하지 않습니다."}, status=404)
        # 관련된 데이터 삭제 (비동기 ORM)
        await sync_to_async(ChatSession.objects.filter(session_id=session_id).delete)()
        await sync_to_async(HistoryChat.objects.filter(session__session_id=session_id).delete)()

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status=500)