# chatting router(chat_api/tts_api/stt_api)
import os
import re
import json
import uuid
import asyncio
import markdown
import tempfile
from pydub import AudioSegment
from fast_api.lcel.lcel import mkch
from fast_api.utils.speech import SpeechProcessor
from fast_api.utils.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import APIRouter, Depends, Request, UploadFile, File
from chat.models import ChatSession, HistoryChat
from asgiref.sync import sync_to_async  # Django ORM을 비동기 함수에서 실행

router = APIRouter()
# stt,tts
speech_processor = SpeechProcessor()

def get_session_data(request: Request):
    """비회원 세션 데이터 관리 함수"""
    session_data = request.cookies.get("chat_session")
    if session_data:
        return json.loads(session_data)
    return {"chat_history": [], "chat_finished": False}

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

@router.post("/chat_api/")
async def chat_api(request: Request, session_id: str, images: list[UploadFile] = File([]), session_data: dict = Depends(get_session_data)):
    """채팅 로직"""
    try:
        # 요청 JSON 데이터 가져오기
        data = await request.json()
        text_input = data.get("message", "").strip()

        # 사용자 ID 받아오기
        chat_session = await sync_to_async(ChatSession.objects.get)(session_id=session_id)
        user_id = chat_session.user_id if chat_session else None
        
        # 로그인 안한 사용자는 채팅 한 번 가능
        if not user_id:
            if session_data["chat_finished"]:
                return JSONResponse({"success": False, "error": "채팅을 이용하려면 로그인 하시오."}, status=400)
            
            # 비회원 세션 채팅 내역 저장
            if "chat_history" not in session_data:
                session_data["chat_history"] = [] # 채팅 내역 초기화

            session_data["chat_finished"] = True
        
        # 로그인한 사용자
        else:
            # 세션 조회
            chat_session = await sync_to_async(ChatSession.objects.get)(user_id=user_id, session_id=session_id)
            # 사용자의 포인트 확인
            user = chat_session.user
            if user.points < 10:
                return JSONResponse({"success": False, "error": "채팅을 하려면 최소 쿠키 10개가 필요합니다."}, status=400)
            # history_id 조회
            history_record = await sync_to_async(HistoryChat.objects.filter(session=chat_session).first)()
            history_id = str(history_record.history_id) if history_record else str(uuid.uuid4())

            # 대화 내역 불러오기
            existing_messages = json.loads(history_record.messages) if history_record else []

        # 이미지 업로드 처리
        image_urls, detected_ingredients = await upload_images(images)

        # 최종 Query 구성
        query_with_ingredients = f"{text_input} 감지된 재료: {', '.join(sorted(detected_ingredients))}" if detected_ingredients else text_input

        # 챗봇 호출
        retriever_filter = data.get("retriever_filter", {"isref": False, "isfun": False, "isman": False})
        cchain = mkch(retriever_filter['isref'], retriever_filter['isfun'], retriever_filter['isman'])

        # AI 응답 생성 (이전 대화 내역을 포함하여 LangChain에 전달)
        async def event_stream():
            outputs = ""
            try:
                async for chunk in cchain.astream(
                    {"question": query_with_ingredients, "history": existing_messages if user_id else session_data["chat_history"]},
                    config={"configurable": {"user_id": user_id, "history_id": history_id if user_id else str(uuid.uuid4())}}
                ):
                    output = chunk['output']
                    formatted_output = format_markdown(output)  # ✅ Markdown 변환 추가
                    outputs += formatted_output
                    yield f"{formatted_output}\n\n"
                    await asyncio.sleep(0.1)
            except Exception as e:
                yield f"Error: {e}"
            finally:
                if user_id:
                    # 기존 대화 내역 저장 (회원)
                    existing_messages.append({"role": "human", "content": text_input})
                    existing_messages.append({"role": "ai", "content": outputs})
                    existing_messages = existing_messages[-10:]
                    if history_record:
                        history_record.messages = json.dumps(existing_messages, ensure_ascii=False)
                        await sync_to_async(history_record.save)()
                    else:
                        await sync_to_async(HistoryChat.objects.create)(user_id=user_id, session=chat_session, history_id=history_id, messages=json.dumps(existing_messages, ensure_ascii=False))

                    # 포인트 차감
                    user.points -= 10
                    await sync_to_async(user.save)()
                else:
                    # 비회원 - 세션에만 저장
                    session_data["chat_history"].append({"role": "human", "content": text_input})
                    session_data["chat_history"].append({"role": "ai", "content": outputs})
                # TTS 파일 생성
                audio_path = await sync_to_async(speech_processor.generate_speech)(outputs, user_id)
                audio_url = f"/{audio_path}" if audio_path else None
            # 최종 응답 반환
            yield f"data: {json.dumps({'success': True, 'message': outputs, 'chat_history': existing_messages if user_id else session_data['chat_history'], 'detected_ingredients': list(detected_ingredients), 'image_urls': image_urls, 'current_points': user.points if user_id else None, 'audio_url': audio_url})}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream;charset=UTF-8")

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

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

@router.post("/stt_api/")
async def stt_api(audio: UploadFile = File(...)):
    """음성 -> 텍스트 변환"""
    temp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    try:
        # 업로드된 음성 저장
        with open(temp_webm.name, "wb") as f:
            f.write(await audio.read())

        # wav 파일로 변환
        audio = AudioSegment.from_file(temp_webm.name)
        audio.export(temp_wav.name, format="wav")

        # Whisper API 호출 전 파일 닫기
        temp_wav.close()

        # Whisper로 변환 (Whisper가 파일을 열 때, 열려 있지 않도록)
        text_result = speech_processor.transcribe_audio(temp_wav.name)
    except Exception as e:
        print(f"STT 오류 발생: {e}")
        return JSONResponse({"error": f"STT 변환 오류: {str(e)}"}, status=500)
    finally:
        # 파일 삭제 전 반드시 닫혔는지 확인
        try:
            temp_webm.close()
            temp_wav.close()
        except:
            pass  # 이미 닫혔으면 무시
        # 이제 파일을 안전하게 삭제
        if os.path.exists(temp_webm.name):
            os.remove(temp_webm.name)
        if os.path.exists(temp_wav.name):
            os.remove(temp_wav.name)

    return JSONResponse({"text": text_result})

@router.post("/tts_api/")
async def tts_api(request: Request):
    """텍스트 -> 음성 변환"""
    data = await request.json()
    text = data.get("text")
    user_id = data.get("user_id", "default_user")

    if text:
        audio_path = speech_processor.generate_speech(text, user_id)
        if audio_path:
            print(f"TTS 파일 생성 완료: {audio_path}")  # 파일 경로 확인용 로그
            return JSONResponse({"audio_url": f"/{audio_path}" if audio_path else ""})  # URL 수정
    return JSONResponse({"error": "Invalid request"}, status_code=400)