import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from chat.lcel.lcel import mkch
from chat.utils.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수
from chat.models import ChatSession, HistoryChat
import markdown
import re
import uuid
import tempfile
from chat.utils.speech import SpeechProcessor
from pydub import AudioSegment


# stt,tts
speech_processor = SpeechProcessor()

# 채팅 페이지 렌더링
def chat_view(request):
    if "chat_history" not in request.session or request.GET.get("new_chat"):
        request.session["chat_history"] = [] # 세션 초기화
    return render(request, "chat.html", {"chat_history": request.session["chat_history"]})

@csrf_exempt
def chat_api(request, session_id):
    if request.method == "POST":
        try:
            # 사용자 ID 받아오기
            user_id = request.user.user_id if request.user.is_authenticated else None
            
            # 로그인 안한 사용자는 채팅 한 번 가능
            if not user_id:
                if "chat_history" not in request.session or request.session.get("chat_finished", False):
                    return JsonResponse({"success": False, "error": "채팅을 이용하려면 로그인 하시오."}, status=400)
                
                if "chat_history" not in request.session:
                    request.session["chat_history"] = [] # 채팅 내역 초기화

                text_input = request.POST.get("message", "").strip()
                print("Received message:", text_input)
                
                image_urls = None
                detected_ingredients = set()

                if text_input:
                    query_with_ingredients = text_input
                else:
                    query_with_ingredients = ""

                # 리트리버
                retriever_filter = request.session.get("retriever_filter", {"isref": False, "isfun": False, "isman": False})
                
                # Chatbot 인스턴스 생성
                cchain = mkch(retriever_filter['isref'], retriever_filter['isfun'], retriever_filter['isman'])

                # AI 응답 생성
                response = cchain.invoke(
                    {"question": query_with_ingredients, "history": request.session["chat_history"]},
                    config={"configurable": {"user_id": None, "history_id": str(uuid.uuid4())}}  # 임시 사용자로 설정
                )

                formatted_response = format_markdown(response)

                # 기존 대화 내역을 유지하면서 새 메시지 추가
                request.session["chat_history"].append({"role": "human", "content": text_input})  # 사용자 입력 추가
                request.session["chat_history"].append({"role": "ai", "content": formatted_response})  # AI 응답 추가

                # 채팅 기록을 한 번만 허용하고 세션 초기화
                request.session["chat_finished"] = True

                # 응답 반환
                return JsonResponse({
                    "success": True,
                    "message": formatted_response,
                    "chat_history": request.session["chat_history"],
                    "detected_ingredients": list(detected_ingredients),
                    "image_urls": image_urls
                })
            
            # 로그인 한 사용자
            else:
                # 사용자의 포인트 체크
                user = request.user
                current_points = user.points
                if user.points < 10:
                    return JsonResponse({"success": False, "error": "채팅을 하려면 최소 쿠키 10개가 필요합니다."}, status=400)

                # 세션 조회
                chat_session = ChatSession.objects.get(user_id=user_id, session_id=session_id)

                # history_id 조회
                history_record = HistoryChat.objects.get(user_id=user_id, session_id=chat_session)
                history_id = str(history_record.history_id)

                # 대화 내역 불러오기
                try:
                    history_record, _ = HistoryChat.objects.get_or_create(user_id=user_id, session=chat_session, defaults={"messages": json.dumps([])})
                    existing_messages = json.loads(history_record.messages)
                except json.JSONDecodeError:
                    existing_messages = []

                # 입력 값 처리
                text_input = request.POST.get("message", "").strip()
                detected_ingredients = set()
                image_urls = []

                # 이미지 업로드 처리
                if "images" in request.FILES:
                    image_files = request.FILES.getlist("images")
                    upload_dir = "media/uploads/"
                    os.makedirs(upload_dir, exist_ok=True)

                    for image_file in image_files:
                        image_path = os.path.join(upload_dir, image_file.name)
                        with open(image_path, "wb") as f:
                            for chunk in image_file.chunks():
                                f.write(chunk)
                        
                        detected_ingredients.update(detect_ingredients(image_path))
                        image_urls.append(f"/media/uploads/{image_file.name}")

                # 최종 Query 구성
                query_with_ingredients = f"{text_input} 감지된 재료: {', '.join(sorted(detected_ingredients))}" if detected_ingredients else text_input

                retriever_filter = request.session.get("retriever_filter", {"isref": False, "isfun": False, "isman": False})

                # Chatbot 인스턴스 생성
                cchain = mkch(retriever_filter['isref'], retriever_filter['isfun'], retriever_filter['isman'])

                # AI 응답 생성 (이전 대화 내역을 포함하여 LangChain에 전달)
                response = cchain.invoke(
                    {"question": query_with_ingredients, "history": existing_messages},
                    config={"configurable": {"user_id": user_id, "history_id": history_id}},
                )

                formatted_response = format_markdown(response)

                # 기존 대화 내역을 유지하면서 새 메시지 추가
                existing_messages.append({"role": "human", "content": text_input})  # 사용자 입력 추가
                existing_messages.append({"role": "ai", "content": formatted_response})  # AI 응답 추가

                existing_messages = existing_messages[-10:]
                
                # 업데이트된 대화 기록을 저장
                history_record.messages = json.dumps(existing_messages, ensure_ascii=False)
                history_record.save()

                #  TTS 파일 자동 생성
                audio_path = speech_processor.generate_speech(response, user_id)
                audio_url = f"/{audio_path}" if audio_path else None 

                # 포인트 차감
                user.points -= 10
                user.save()  # 포인트 변경 사항 저장

                # 응답 반환
                return JsonResponse({
                    "success": True,
                    "message": formatted_response,
                    "chat_history": existing_messages,
                    "detected_ingredients": list(detected_ingredients),
                    "image_urls": image_urls,
                    "current_points": current_points,
                    "audio_url": audio_url,
                })
        except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

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


@login_required
@csrf_exempt
def new_chat(request):
    """새로운 채팅을 생성하고 ID 반환"""
    if request.method == "POST":
        chat_session = ChatSession.objects.create(user=request.user)

        # 새로운 세션에 대해 HistoryChat도 생성
        history = HistoryChat.objects.create(
            user=request.user,
            session=chat_session,
            title="",
            messages=json.dumps([])  # 빈 메시지 리스트 저장
        )
        # 세션 초기화
        request.session["chat_history"] = []

        return JsonResponse({
            "success": True,
            "chat_id": str(chat_session.session_id),
            "title": history.title 
        })

    return JsonResponse({"success": False}, status=400)

@login_required
def chat_sessions(request):
    """사용자의 모든 채팅 세션을 불러오기"""
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")

    session_data = []
    for session in sessions:
        history = HistoryChat.objects.filter(session=session).first()
        title = history.title if history else "새로운 대화"
        
        first_chat = HistoryChat.objects.filter(session=session).order_by("created_at").first()
        # 첫 번째 human 메시지를 찾기
        if first_chat:
            messages = json.loads(first_chat.messages)
            first_human_message = next((msg["content"] for msg in messages if msg["role"] == "human"), "대화 요약 없음")
        else:
            first_human_message = "대화 요약 없음"
        summary = first_human_message[:15] 

        session_data.append({
            "session_id": str(session.session_id),
            "title": title,
            "summary": summary,
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return JsonResponse({"success": True, "sessions": session_data})

@login_required
def chat_history(request, session_id):
    """특정 세션의 채팅 내역을 불러옴"""
    try:
        chat_session = ChatSession.objects.get(session_id=session_id)
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "채팅 세션을 찾을 수 없습니다."}, status=404)

    history = HistoryChat.objects.filter(session=chat_session).first()
    if not history:
        return JsonResponse({"session_id": session_id, "messages": []})  # 기록이 없을 경우 빈 리스트 반환

    try:
        messages = json.loads(history.messages)  # JSON 데이터를 리스트로 변환
    except json.JSONDecodeError:
        messages = []  # 데이터 변환 실패 시 빈 리스트 반환

    message_list = []
    for msg in messages:
        message_list.append({
            "content": msg["content"],  # JSON 형식 그대로 반환
            "sender": "User" if msg["role"] == "human" else "AI",
        })

    return JsonResponse({
        "session_id": session_id,
        "messages": message_list
    })


@login_required
def delete_chat(request, session_id):
    """특정 채팅 세션 삭제"""
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)
        
        # 관련된 모든 데이터 삭제
        ChatSession.objects.filter(session_id=session_id).delete()  # session_id로 필터링
        HistoryChat.objects.filter(session__session_id=session_id).delete()  # session의 session_id로 필터링
        session.delete()

        return JsonResponse({"success": True})
    except ChatSession.DoesNotExist:
        return JsonResponse({"success": False, "error": "세션이 존재하지 않습니다."}, status=404)
    
@csrf_exempt
def stt_api(request):
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]

        temp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

        try:
            # 업로드된 음성 저장
            with open(temp_webm.name, "wb") as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)

            # wav 파일로 변환
            audio = AudioSegment.from_file(temp_webm.name)
            audio.export(temp_wav.name, format="wav")

            # Whisper API 호출 전 파일 닫기 (중요!)
            temp_wav.close()

            # Whisper로 변환 (Whisper가 파일을 열 때, 열려 있지 않도록)
            text_result = speech_processor.transcribe_audio(temp_wav.name)

        except Exception as e:
            print(f"STT 오류 발생: {e}")
            return JsonResponse({"error": f"STT 변환 오류: {str(e)}"}, status=500)

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

        return JsonResponse({"text": text_result})

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def tts_api(request):
    """🔊 TTS API: 입력된 텍스트를 음성으로 변환"""
    if request.method == "POST":
        text = request.POST.get("text")
        user_id = request.POST.get("user_id", "default_user")

        if text:
            audio_path = speech_processor.generate_speech(text, user_id)
            if audio_path:
                print(f"TTS 파일 생성 완료: {audio_path}")  # 🔎 파일 경로 확인용 로그
                return JsonResponse({"audio_url": f"/{audio_path}"})  # 🔥 URL 수정
            return JsonResponse({"audio_url": audio_path})

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def update_retriever(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            isman = data.get("isman", False)
            isfun = data.get("isfun", False)
            isref = data.get("isref", False)

            request.session["retriever_filter"] = {"isman": isman, "isfun": isfun, "isref": isref}

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)