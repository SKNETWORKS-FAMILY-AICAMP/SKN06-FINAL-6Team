import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from chat.lcel.lcel import mkch
from chat.utils.memories import mkhisid
from chat.utils.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from chat.models import Chats, ChatSession
import markdown
import re

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
            user_id = request.user.user_id if request.user.is_authenticated else 0
            chat_history = request.session.get("chat_history", [])
            max_history = 5  # 최근 5개만 유지 (너무 길어지는 문제 방지)

            # 텍스트 입력 처리
            text_input = request.POST.get("message", "").strip()

            # 이미지 파일 처리
            detected_ingredients = set()
            image_path = None  # 기본값 설정

            if "image" in request.FILES:
                image_file = request.FILES["image"]

                # `media/uploads/` 폴더가 없으면 생성
                upload_dir = "media/uploads/"
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)

                image_path = os.path.join(upload_dir, image_file.name)

                # 파일 저장 (경로 지정)
                with open(image_path, "wb") as f:
                    for chunk in image_file.chunks():
                        f.write(chunk)

                # YOLO 감지 수행 (이미지 저장 후 실행)
                detected_ingredients.update(detect_ingredients(image_path))

            # 감지된 재료 정리 (중복 제거)
            detected_ingredients = sorted(set(detected_ingredients))

            # 최근 5개만 유지하여 대화 길이 제한
            recent_history = chat_history[-max_history:]

            # 이전 감지된 재료가 있으면 최신화
            previous_ingredients = set()
            for entry in recent_history:
                if "detected_ingredients" in entry:
                    previous_ingredients.update(entry["detected_ingredients"])
            
            # 새로운 재료와 기존 재료를 합쳐서 중복 방지
            all_ingredients = sorted(previous_ingredients.union(detected_ingredients))

            # 최종 Query 구성 (이전 대화 포함하되, 너무 길어지지 않도록 제한)
            image_url = f"/media/uploads/{image_file.name}" if image_path else None
            if all_ingredients:
                query_with_ingredients = f"다음 재료를 사용하여 레시피를 추천해 주세요: {', '.join(all_ingredients)}"
            else:
                query_with_ingredients = text_input

            # AI 응답 생성
            history_id = mkhisid(user_id)
            response = cchain.invoke(
                {"question": query_with_ingredients},
                config={"configurable": {"user_id": user_id, "history_id": history_id}},
            )
            formatted_response = format_markdown(response)

            # 대화 기록 업데이트 (최근 5개만 유지)
            chat_history.append({
                "user": text_input,
                "bot": response,
                "image": image_url,
                "detected_ingredients": all_ingredients  # 감지된 재료 포함
            })
            chat_history = chat_history[-max_history:]  # 최근 5개 유지
            request.session["chat_history"] = chat_history  # 세션에 저장

            # 응답 반환
            return JsonResponse({
                "success": True,
                "message": formatted_response,
                "chat_history": chat_history,
                "detected_ingredients": all_ingredients
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

# 새 채팅 시작 (기존 대화 초기화)
@login_required
@csrf_exempt
def new_chat(request):
    request.session["chat_history"] = []  # 기존 대화 삭제
    return JsonResponse({"success": True, "message": "새 채팅이 시작되었습니다.", "chat_history": []})


@login_required
def chat_sessions(request):
    """Retrieve chat session list for user"""
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")
    session_data = []

    for session in sessions:
        latest_chat = Chats.objects.filter(session=session).order_by("-created_at").first()
        summary = latest_chat.question_content[:30] if latest_chat else "No messages"

        session_data.append({
            "session_id": str(session.session_id),
            "summary": summary,
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return JsonResponse({"sessions": session_data})

@login_required
def chat_history(request, session_id):
    """Load specific chat session history"""
    try:
        chat_session = ChatSession.objects.get(session_id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    messages = Chats.objects.filter(session=chat_session).order_by("created_at")
    message_list = [
        {"sender": "User", "content": msg.question_content} for msg in messages
    ] + [
        {"sender": "AI", "content": msg.response_content} for msg in messages if msg.response_content
    ]

    return JsonResponse({"session_id": session_id, "messages": message_list})

@login_required
def delete_chat(request, session_id):
    """특정 채팅 세션 삭제"""
    try:
        session = ChatSession.objects.filter(session_id=session_id, user=request.user).first()
        session.delete()
        return JsonResponse({"success": True})
    except ChatSession.DoesNotExist:
        return JsonResponse({"success": False, "error": "세션이 존재하지 않습니다."}, status=404)
