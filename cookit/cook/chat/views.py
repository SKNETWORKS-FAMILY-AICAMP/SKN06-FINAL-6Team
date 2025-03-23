import os
import re
import uuid
import json
import tempfile
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from chat.models import ChatSession, HistoryChat, UserSelectedMenus, ManRecipes, FridgeRecipes, FunsRecipes
from chat.utils.fastapi_client import call_fastapi_chat, call_fastapi_stt, call_fastapi_tts, call_fastapi_image_detect

# 채팅 페이지 렌더링
def chat_view(request):
    if "chat_history" not in request.session or request.GET.get("new_chat"):
        request.session["chat_history"] = []  # 세션 초기화

    return render(request, "chat.html", {"chat_history": request.session["chat_history"]})

@csrf_exempt
def chat_api(request, session_id):
    """Django에서 FastAPI로 채팅 요청을 보내고 응답을 저장"""
    if request.method == "POST":
        try:
            user = request.user if request.user.is_authenticated else None
            text_input = request.POST.get("message", "").strip()

            # 비회원 처리
            if not user:
                if "chat_history" not in request.session or request.session.get("chat_finished", False):
                    return JsonResponse({"success": False, "error": "채팅을 이용하려면 로그인 하시오."}, status=400)

                request.session.setdefault("chat_history", [])  # 채팅 내역 초기화
                request.session["chat_finished"] = True  # 비회원은 1회만 가능

                chat_response = call_fastapi_chat(message=text_input, user_id=None, history_id=str(uuid.uuid4()), chat_history=request.session["chat_history"])

                # django 세션에 채팅 기록 저장
                request.session["chat_history"].append({"role": "human", "content": text_input})
                request.session["chat_history"].append({"role": "ai", "content": chat_response["message"]})

                return JsonResponse(chat_response)

            # 회원 처리
            if user.points < 10:
                return JsonResponse({"success": False, "error": "채팅을 하려면 최소 쿠키 10개가 필요합니다."}, status=400)

            # 세션, 대화 내역 조회
            chat_session = ChatSession.objects.get(user_id=user.id, session_id=session_id)
            history_record, _ = HistoryChat.objects.get_or_create(
                user_id=user.id, session=chat_session, defaults={"messages": json.dumps([])}
            )
            existing_messages = json.loads(history_record.messages)

            # 이미지 업로드 FastAPI 호출
            image_urls = []
            detected_ingredients = []
            if "images" in request.FILES:
                image_files = request.FILES.getlist("images")
                image_response = call_fastapi_image_detect(image_files)  # 이미지를 FastAPI로 전송
                if "error" not in image_response:
                    image_urls = image_response.get("image_urls", [])
                    detected_ingredients = image_response.get("detected_ingredients", [])

            # `text_input` + `image_response` (이미지 감지된 재료 포함)
            query_with_ingredients = f"{text_input} 감지된 재료: {', '.join(sorted(detected_ingredients))}" if detected_ingredients else text_input

            # FastAPI에 채팅 요청
            chat_response = call_fastapi_chat(message=query_with_ingredients, user_id=user.id, history_id=str(history_record.history_id), chat_history=existing_messages)

            # 대화 내역 저장
            existing_messages.append({"role": "human", "content": text_input})
            existing_messages.append({"role": "ai", "content": chat_response["message"]})
            history_record.messages = json.dumps(existing_messages, ensure_ascii=False)
            history_record.save()

            # TTS 생성
            tts_response = call_fastapi_tts(chat_response["message"], user.id)
            chat_response["audio_url"] = tts_response.get("audio_url")

            # 포인트 차감 후 저장
            user.points -= 10
            user.save()

            return JsonResponse(chat_response)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

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
    """STT API: 음성을 FastAPI로 보내 변환된 텍스트를 받음"""
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
        try:
            # 업로드된 음성 저장
            with open(temp_audio.name, "wb") as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)
            # FastAPI에 STT 요청 보내기
            with open(temp_audio.name, "rb") as f:
                stt_response = call_fastapi_stt(f)
        except Exception as e:
            return JsonResponse({"error": f"STT 변환 오류: {str(e)}"}, status=500)
        finally:
            # 임시 파일 삭제
            os.remove(temp_audio.name)
        return JsonResponse(stt_response)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def tts_api(request):
    """TTS API: 텍스트를 FastAPI로 보내 변환된 음성 파일을 받음"""
    if request.method == "POST":
        text = request.POST.get("text")
        user_id = request.POST.get("user_id", "default_user")
        if text:
            tts_response = call_fastapi_tts(text, user_id)
            return JsonResponse(tts_response)
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

def get_recipe_source_and_id(menu_name=None, img_url=None):
    print(f"🔹 get_recipe_source_and_id 실행됨: menu_name={menu_name}, img_url={img_url}")

    for model, source_name in [
        (ManRecipes, "ManRecipes"),
        (FridgeRecipes, "FridgeRecipes"),
        (FunsRecipes, "FunsRecipes"),
    ]:
        
        img_field = "img"  # 기본값으로 'img' 사용
        if not hasattr(model, "img"):  # 'img'가 없으면 'image' 사용
            img_field = "image"

        if img_url:
            filter_params = {img_field: img_url}  # 동적으로 필드 이름을 설정
            recipe = model.objects.filter(**filter_params).first()
        else:
            recipe = model.objects.filter(name=menu_name).first()

        if recipe:
            print(f"찾은 레시피: ID={recipe.id}, Source={source_name}")
            return recipe.id, source_name

    print("❌ 데이터 없음")
    return None, None


@csrf_exempt
def save_user_selected_menus(request, session_id):
    print("🔹 save_user_selected_menus 실행됨")

    chat_session = ChatSession.objects.filter(session_id=session_id, user=request.user).first()
    if not chat_session:
        print("❌ Chat session not found")
        return JsonResponse({"success": False, "error": "Chat session not found."}, status=404)

    history = HistoryChat.objects.filter(session=chat_session).first()
    if not history:
        print("❌ No chat history found")
        return JsonResponse({"success": False, "error": "No chat history found."}, status=404)

    try:
        messages = json.loads(history.messages) if history.messages else []
        print(f" 불러온 채팅 메시지: {messages}")  # 🚀 AI 응답 확인용 로그 추가
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in chat history")
        return JsonResponse({"success": False, "error": "Invalid JSON format in chat history"}, status=500)

    recipe_pattern = re.compile(r"<h3>\d+\.\s*([^<\n]+)")  # 🚀 정규식 개선
    img_pattern = re.compile(r'https://[^"\s<]+')

    recipe_names = set()
    recipe_images = {}

    for message in messages:
        if message["role"] == "ai":
            menu_names = recipe_pattern.findall(message["content"])
            recipe_names.update(menu_names)

            img_urls = img_pattern.findall(message["content"])

            for i, menu_name in enumerate(menu_names):
                img_url = img_urls[i] if i < len(img_urls) else None
                recipe_images[menu_name] = img_url

    print(f"추출된 메뉴명: {recipe_names}")
    print(f"추출된 이미지 URL: {recipe_images}")

    if not recipe_names:
        print("❌ 추출된 메뉴명이 없습니다. 정규식 패턴을 다시 확인하세요.")

    for menu_name in recipe_names:
        img_url = recipe_images.get(menu_name, None)
        recipe_id, source = get_recipe_source_and_id(menu_name=menu_name, img_url=img_url)

        print(f"저장 시도: 메뉴명={menu_name}, 이미지={img_url}, source={source}, recipe_id={recipe_id}")

        obj, created = UserSelectedMenus.objects.get_or_create(
            user=request.user,
            menu_name=menu_name,
            defaults={"img_url": img_url, "recipe_id": recipe_id, "source": source}
        )

        if not created:
            updated = False
            if obj.img_url != img_url:
                obj.img_url = img_url
                updated = True
            if obj.recipe_id != recipe_id:
                obj.recipe_id = recipe_id
                updated = True
            if obj.source != source:
                obj.source = source
                updated = True
            if updated:
                obj.save()

        if created:
            print(f"저장 성공: {menu_name} with image {img_url}, source: {source}, recipe_id: {recipe_id}")

    return JsonResponse({"success": True, "saved_menus": list(recipe_names), "saved_images": recipe_images})