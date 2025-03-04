from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse,HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Chats, HistoryChat, ChatRecommendations, ManRecipes, FridgeRecipes, FunsRecipes
import json
from .llm import mkch
import random
# LLM 체인 생성

llm_chain = mkch()
def get_recommended_recipe():
    sources = [ManRecipes, FridgeRecipes, FunsRecipes]
    selected_model = random.choice(sources)
    recipe = selected_model.objects.order_by("?").first()
    return recipe

def get_user_chat_history(user_id):
    """사용자의 기존 채팅 기록 ID를 가져오거나, 없으면 새로 생성"""
    chat_history = HistoryChat.objects.filter(user_id=user_id).order_by('-created_at').first()
    
    if chat_history:
        return chat_history.history_id  # 기존 기록 반환
    else:
        # 새 히스토리 생성 후 반환
        new_chat = HistoryChat.objects.create(user_id=user_id, question_content="", response_content="")
        return new_chat.history_id

def chat_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get('question')

            # 비회원 여부 확인
            if request.user.is_authenticated:
                user_id = request.user.user_id  # 로그인한 사용자 ID
                history_id = get_user_chat_history(user_id)  # 기존 히스토리 조회 or 생성
            else:
                user_id = None  # 비회원은 ID 없음
                history_id = None  # 비회원은 채팅 기록 없음

            # 비회원일 경우에도 `config`에서 None을 허용하도록 수정
            response = llm_chain.invoke(
                {'question': question}, 
                config={'configurable': {'user_id': user_id or 'guest', 'history_id': history_id or 'guest'}}
            )

            return JsonResponse({"response": response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    # 🔹 GET 요청 처리: 채팅 화면 렌더링
    return render(request, "chat/chat.html")



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

            if not request.user.is_authenticated:
                if request.session.get("question_asked", False):
                    return JsonResponse({"error": "비회원 사용자는 한 번만 질문할 수 있습니다."}, status=403)
                request.session["question_asked"] = True

            response = llm_chain.invoke({"question": user_message})

            chat = Chats.objects.create(
                user=request.user if request.user.is_authenticated else None,
                question_content=user_message,
                response_content=response
            )

            if request.user.is_authenticated:
                recommended_recipe = get_recommended_recipe()
                ChatRecommendations.objects.create(
                    chat=chat,
                    user=request.user,
                    recommended_menu_id=recommended_recipe.recipe_id
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
