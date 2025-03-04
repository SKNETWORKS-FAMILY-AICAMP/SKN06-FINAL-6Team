from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Chats, HistoryChat, ChatRecommendations
import json
from .llm import mkch
# LLM 체인 생성
llm_chain = mkch()

# 비회원은 historychat을 볼 수 없음. 로그인된 사용자만 자신의 채팅 세션을 조회 가능.
def chat_view(request):
    chat_sessions = Chats.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, "chat/chat.html", {"chat_sessions": chat_sessions})

# 새로운 채팅을 시작할 때 기존 채팅을 HistoryChat으로 이전.
# 비회원은 새로운 채팅을 시작할 수 없음.
@login_required
def new_chat(request):
    if request.method == "POST":
        existing_chats = Chats.objects.filter(user=request.user)
        for chat in existing_chats:
            HistoryChat.objects.create(
                user=chat.user,
                question_content=chat.question_content,
                response_content=chat.response_content
            )
            chat.delete()  # 기존 채팅 삭제
        
        chat = Chats.objects.create(user=request.user, question_content="새 채팅 시작", response_content="")
        return JsonResponse({"success": True, "chat_id": chat.chat_id})
    return JsonResponse({"success": False}, status=400)

# 비회원은 한 번의 질문과 한 번의 응답만 받을 수 있음.
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            if not user_message:
                return JsonResponse({"error": "메시지를 입력해주세요."}, status=400)
            
            # 비회원이 한 번 질문했는지 확인
            if not request.user.is_authenticated:
                if request.session.get("question_asked", False):
                    return JsonResponse({"error": "비회원 사용자는 한 번만 질문할 수 있습니다."}, status=403)
                request.session["question_asked"] = True
            
            response = generate_chat_response(user_message)
            chat = Chats.objects.create(
                user=request.user if request.user.is_authenticated else None,
                question_content=user_message,
                response_content=response
            )
            
            # AI 추천 메뉴를 ChatRecommendations에 저장 (비회원은 저장 안 됨)
            if request.user.is_authenticated:
                ChatRecommendations.objects.create(
                    chat=chat,
                    user=request.user,
                    recommended_menu_id=1  # 임시 데이터, 실제 추천 로직 필요
                )
            
            return JsonResponse({"response": response, "chat_id": chat.chat_id})
        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)
    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)

# 로그인된 사용자만 자신의 채팅 세션을 조회 가능.
@login_required
def chat_sessions(request):
    sessions = Chats.objects.filter(user=request.user).order_by("-created_at")
    return JsonResponse({
        "sessions": list(sessions.values("chat_id", "question_content"))
    })

# 로그인된 사용자만 채팅을 삭제 가능.
@login_required
def delete_chat(request, chat_id):
    try:
        chat = Chats.objects.get(chat_id=chat_id, user=request.user)
        HistoryChat.objects.create(
            user=chat.user,
            question_content=chat.question_content,
            response_content=chat.response_content
        )
        chat.delete()
        return JsonResponse({"success": True})
    except Chats.DoesNotExist:
        return JsonResponse({"success": False, "error": "채팅이 존재하지 않습니다."}, status=404)

# 사용자 최종 선택 요리는 별도의 행동을 정한 후 저장 예정.
# 현재는 ChatRecommendations에 AI가 추천한 메뉴만 저장하고, UserSelectedMenus 저장 로직은 추후 추가.
@login_required
def save_final_recipe(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = request.user
            recipe_id = data.get("recipe_id")
            
            # 추천 요리 업데이트 (최종 선택 아님, 단순 추천 저장)
            recommendation = ChatRecommendations.objects.filter(user=user, recommended_menu_id=recipe_id).first()
            if recommendation:
                recommendation.selected = True
                recommendation.save()
            else:
                ChatRecommendations.objects.create(user=user, recommended_menu_id=recipe_id, selected=True)
            
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)
