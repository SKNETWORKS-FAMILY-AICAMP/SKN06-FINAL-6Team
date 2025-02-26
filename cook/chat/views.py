from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Message
from .llm import mkch  # LLM 연결
import json

# LLM 체인 생성
llm_chain = mkch()

def chat_view(request):
    """채팅 페이지 렌더링"""
    question_asked = request.session.get("question_asked", False)

    return render(request, "chat/chat.html", {"question_asked": question_asked})

def chat_api(request):
    """사용자의 입력을 받아 LLM을 호출하고 응답을 반환하는 API"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"error": "메시지를 입력해주세요."}, status=400)

            # 비회원이 한 번 질문했는지 확인 (세션 기반)
            if not request.user.is_authenticated and request.session.get("question_asked", False):
                return JsonResponse({"error": "비회원 사용자는 한 번만 질문할 수 있습니다."}, status=403)

            # LLM 호출
            response = llm_chain.invoke({"question": user_message})

            # 로그인한 사용자만 메시지 저장
            if request.user.is_authenticated:
                Message.objects.create(user=request.user, content=user_message)
                Message.objects.create(user=request.user, content=response)  # AI 응답 저장

            # 비회원이라면 세션에 질문 여부 저장
            if not request.user.is_authenticated:
                request.session["question_asked"] = True

            return JsonResponse({"response": response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)
