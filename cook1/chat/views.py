import re
import os
import uuid
import json
import markdown
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from chat.lcel.lcel import mkch
from chat.utils.memories import mkhisid
from chat.utils.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수
from chat.models import Chats, ChatSession, HistoryChat

# Chatbot 인스턴스 생성
cchain = mkch()

# 채팅 페이지 렌더링
def chat_view(request):
    if "chat_history" not in request.session:
        request.session["chat_history"] = []
    return render(request, "chat.html", {"chat_history": request.session["chat_history"]})

@csrf_exempt
def chat_api(request):
    if request.method == "POST":
        try:
            # 사용자 ID 받아오기
            user_id = request.user.user_id if request.user.is_authenticated else None
            if not user_id:
                return JsonResponse({"success": False, "error": "로그인이 필요합니다."}, status=403)

            # 기존 세션 조회 또는 생성
            chat_session = ChatSession.objects.filter(user_id=user_id).order_by("-created_at").first()
            if not chat_session:
                chat_session = ChatSession.objects.create(user_id=user_id)

            # 기존 history_id 조회 또는 새로운 UUID 생성
            history_id = mkhisid(user_id)
            if not history_id:
                history_id = str(uuid.uuid4())  # 새로운 UUID 생성

            # 기존 `HistoryChat` 불러오기 (없으면 생성)
            history_record, created = HistoryChat.objects.get_or_create(
                user_id=user_id,
                session=chat_session,
                defaults={"messages": json.dumps([])}  # 기본 빈 리스트
            )

            # 기존 대화 내역 불러오기
            try:
                existing_messages = json.loads(history_record.messages)
            except json.JSONDecodeError:
                existing_messages = []

            # 입력 값 처리
            text_input = request.POST.get("message", "").strip()
            detected_ingredients = set()
            image_url = None

            # 이미지 업로드 처리
            if "image" in request.FILES:
                image_file = request.FILES["image"]
                upload_dir = "media/uploads/"
                os.makedirs(upload_dir, exist_ok=True)
                image_path = os.path.join(upload_dir, image_file.name)

                with open(image_path, "wb") as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

                detected_ingredients.update(detect_ingredients(image_path))
                image_url = f"/media/uploads/{image_file.name}"

            # 감지된 재료 정리
            detected_ingredients = sorted(detected_ingredients)

            # 최종 Query 구성
            if detected_ingredients:
                query_with_ingredients = f"{text_input} 감지된 재료: {', '.join(detected_ingredients)}"
            else:
                query_with_ingredients = text_input

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

            # 응답 반환
            return JsonResponse({
                "success": True,
                "message": formatted_response,
                "chat_history": existing_messages,
                "detected_ingredients": detected_ingredients,
                "image_url": image_url
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

        match = menu_pattern.match(line)
        if match:
            line = f"<h3>{match.group(1)}. {match.group(2)}</h3>"  # 메뉴명을 <h3>로 변환
        
        # `사진:`이 포함된 경우 처리
        elif "사진:" in line:
            parts = line.split("사진:")
            if len(parts) > 1:
                image_url = parts[1].strip()
                if image_url and image_url.startswith("http"):  # URL이 있는 경우에만 처리
                    line = f'<img src="{image_url}" alt="요리 이미지" class="recipe-img" style="width: 250px; height: auto; display: block; margin: 10px auto;">'
        
        # `![이미지](URL)` 패턴을 감지하여 변환
        line = image_pattern.sub(r'<img src="\1" alt="요리 이미지" class="recipe-img" style="width: 250px; height: auto; display: block; margin: 10px auto;">', line)

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
            title="새로운 대화",
            messages=json.dumps([])  # 빈 메시지 리스트 저장
        )

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

        first_chat = Chats.objects.filter(session=session).order_by("created_at").first()
        summary = first_chat.question_content[:30] if first_chat else "대화 요약 없음"

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
            "sender": "User" if msg["role"] == "user" else "AI",
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
        Chats.objects.filter(session=session).delete()
        HistoryChat.objects.filter(session=session).delete()
        session.delete()

        return JsonResponse({"success": True})
    except ChatSession.DoesNotExist:
        return JsonResponse({"success": False, "error": "세션이 존재하지 않습니다."}, status=404)