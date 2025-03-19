# update_retriever router
import json
import base64
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/update_retriever/")
async def update_retriever(request: Request):
    """리트리버 필터 API - 사용자 필터 설정을 쿠키에 저장"""
    try:
        data = await request.json()

        # 값 검증 (True/False가 아닌 값이 들어오면 기본값 False 설정)
        retriever_filter = {"isman": data.get("isman", False), "isfun": data.get("isfun", False), "isref": data.get("isref", False)}
        encoded_filter = base64.b64encode(json.dumps(retriever_filter).encode()).decode()

        response = JSONResponse({"success": True})
        response.set_cookie(key="retriever_filter",
            value=encoded_filter,
            httponly=True,
            secure=True,  # HTTPS 사용 시 보안 강화
            samesite="Lax",  # 크로스사이트 요청 보호
            max_age=3600  # 쿠키 만료 시간 1시간
        )
        return response
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status=500)