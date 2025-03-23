# chating router
import os
import re
import json
import uuid
import asyncio
import markdown
from lcel.lcel import mkch
from utils.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import APIRouter, Request, UploadFile, File

router = APIRouter()

async def upload_images(images: list[UploadFile]) -> tuple[list[str], set]:
    """FastAPI 방식으로 이미지 업로드 및 Object Detection 수행"""
    detected_ingredients = set()
    image_urls = []
    upload_dir = "media/uploads/"
    os.makedirs(upload_dir, exist_ok=True)

    for image in images:
        image_path = os.path.join(upload_dir, image.filename)
        with open(image_path, "wb") as f:
            f.write(await image.read())  # FastAPI는 비동기 방식으로 파일 읽기

        detected_ingredients.update(detect_ingredients(image_path))
        image_urls.append(f"/media/uploads/{image.filename}")

    return image_urls, detected_ingredients

def format_markdown(response):
    """메뉴명만 숫자로 표시하고, 나머지는 일반 텍스트 처리 및 이미지 삽입"""
    lines = response.split("\n")
    formatted_lines = []
    menu_pattern = re.compile(r"^(\d+)\.\s(.*)")  # 메뉴명 패턴 (번호. 제목)
    image_pattern = re.compile(r"!\[.*?\]\((.*?)\)")  # `![이미지](URL)` 패턴 감지

    for line in lines:
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)  # `**` 강조 기호 제거

        # 메뉴명 패턴 적용
        match = menu_pattern.match(line)
        if match:
            line = f"<h3>{match.group(1)}. {match.group(2)}</h3>"  # 메뉴명을 <h3>로 변환
        
        # 사진을 감지하고 이미지로 변환
        line = image_pattern.sub(r'<img src="\1" alt="요리 이미지" class="recipe-img" style="width: 250px; height: auto; display: block; margin: 10px auto;">', line)

        # '재료'나 '사진' 앞에 새 줄 추가
        if "재료" in line or "사진" in line:
            formatted_lines.append("<br>")  # 새 줄 추가

        formatted_lines.append(line)

    return markdown.markdown("\n".join(formatted_lines), extensions=["extra"])

@router.post("/member_chat/")
async def member_chat(request: Request, images: list[UploadFile] = File([])):
    """회원 챗봇 응답 처리 함수"""
    try:
        # 요청 JSON 데이터 가져오기
        data = await request.json()
        text_input = data.get("message", "").strip()
        user_id = data.get("user_id", None)
        history_id = data.get("history_id", str(uuid.uuid4()))
        existing_messages = data.get("chat_history", [])

        # 이미지 업로드 처리
        image_urls, detected_ingredients = await upload_images(images)

        # 최종 Query 구성
        query_with_ingredients = f"{text_input} 감지된 재료: {', '.join(sorted(detected_ingredients))}" if detected_ingredients else text_input

        # 챗봇 호출
        retriever_filter = data.get("retriever_filter", {"isref": False, "isfun": False, "isman": False})
        cchain = mkch(retriever_filter['isref'], retriever_filter['isfun'], retriever_filter['isman'])

        # AI 응답 생성
        async def event_stream():
            outputs = ""
            try:
                async for chunk in cchain.astream(
                    {"question": query_with_ingredients, "history": existing_messages},
                    config={"configurable": {"user_id": user_id, "history_id": history_id}}
                ):
                    output = chunk['output']
                    formatted_output = format_markdown(output)
                    outputs += formatted_output
                    yield f"{formatted_output}\n\n"
                    await asyncio.sleep(0.1)
            except Exception as e:
                yield f"Error: {e}"
            # 최종 응답 반환 (Django에서 이 데이터를 저장)
            yield f"data: {json.dumps({'success': True, 'message': outputs, 'chat_history': existing_messages + [{'role': 'human', 'content': text_input}, {'role': 'ai', 'content': outputs}], 'detected_ingredients': list(detected_ingredients), 'image_urls': image_urls})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream;charset=UTF-8")

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    
@router.post("/guest_chat/")
async def guest_chat(request: Request):
    """비회원 챗봇 응답 처리 함수"""
    try:
        data = await request.json()
        text_input = data.get("message", "").strip()
        user_id = data.get("user_id", None)
        history_id = data.get("history_id", str(uuid.uuid4()))
        existing_messages = data.get("chat_history", [])

        if len(existing_messages) >= 2:  # (질문 + 응답) 한 세트만 가능
            raise HTTPException(status_code=400, detail="비회원은 한 번만 채팅할 수 있습니다.")
        
        # 챗봇 호출
        retriever_filter = data.get("retriever_filter", {"isref": False, "isfun": False, "isman": False})
        cchain = mkch(retriever_filter['isref'], retriever_filter['isfun'], retriever_filter['isman'])

        # AI 응답 생성
        async def event_stream():
            outputs = ""
            try:
                async for chunk in cchain.astream(
                    {"question": text_input, "history": existing_messages},
                    config={"configurable": {"user_id": user_id, "history_id": history_id}}
                ):
                    output = chunk['output']
                    formatted_output = format_markdown(output)
                    outputs += formatted_output
                    yield f"{formatted_output}\n\n"
                    await asyncio.sleep(0.1)
            except Exception as e:
                yield f"Error: {e}"
            
            # 최종 응답 반환 (Django에서 저장)
            yield f"data: {json.dumps({'success': True, 'message': outputs, 'chat_history': existing_messages + [{'role': 'human', 'content': text_input}, {'role': 'ai', 'content': outputs}]})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream;charset=UTF-8")

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)