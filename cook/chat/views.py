from django.shortcuts import render, redirect,get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Message,ChatSession
from django.utils.timezone import localtime
from .llm import mkch  # LLM 연결
import json
import uuid

# LLM 체인 생성
llm_chain = mkch()

def chat_view(request):
    """채팅 페이지 렌더링"""
    question_asked = request.session.get("question_asked", False)
    chat_sessions = ChatSession.objects.filter(user=request.user) if request.user.is_authenticated else []
    
    return render(request, "chat/chat.html", {
        "question_asked": question_asked,
        "chat_sessions": chat_sessions,
    })

@login_required
def new_chat(request):
    """새로운 채팅을 생성하고 ID 반환"""
    if request.method == "POST":
        session_id = str(uuid.uuid4())  # 랜덤한 UUID 생성
        chat_session = ChatSession.objects.create(user=request.user, session_id=session_id)
        
        print(f"✅ 새 채팅 세션 생성됨: {session_id}")  # 디버깅 로그

        return JsonResponse({
            "success": True,
            "chat_id": chat_session.session_id
        })

    return JsonResponse({"success": False}, status=400)

def chat_history(request, session_id):
    """특정 세션의 채팅 내역을 불러옴"""
    chat_session = get_object_or_404(ChatSession, session_id=session_id)
    messages = Message.objects.filter(session=chat_session).order_by("timestamp")

    message_list = []
    for msg in messages:
        # 사용자 입력 메시지 추가
        message_list.append({
            "content": msg.content,
            "sender": "User",  # ✅ 사용자 메시지
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
        # AI 응답이 있다면 추가
        if msg.response:
            message_list.append({
                "content": msg.response,
                "sender": "AI",  # ✅ AI 응답
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })

    return JsonResponse({
        "session_id": session_id,
        "messages": message_list
    })

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

            # 로그인한 사용자만 쿠키 차감
            if request.user.is_authenticated:
                if request.user.point < 10:  # ❌ 쿠키 부족하면 차단
                    return JsonResponse({"error": "쿠키가 부족하여 채팅을 보낼 수 없습니다."}, status=403)

                request.user.point -= 10  # 쿠키 10개 차감
                request.user.save()

            # 🔹 사용자의 채팅 세션 가져오기 (없다면 새로운 세션 생성)
            if request.user.is_authenticated:
                chat_session = ChatSession.objects.filter(user=request.user).order_by("-created_at").first()
                if not chat_session:
                    chat_session = ChatSession.objects.create(user=request.user, session_id=str(uuid.uuid4()))
            else:
                chat_session = ChatSession.objects.create(session_id=str(uuid.uuid4()))  # 비회원도 새로운 세션 생성

            # LLM 호출
            response = llm_chain.invoke({"question": user_message})

            # 메시지 저장 (session 포함)
            Message.objects.create(
                session=chat_session,
                user=request.user if request.user.is_authenticated else None,
                content=user_message,
                response=response  # 🔹 AI 응답을 response 필드에 저장
            )

            # 비회원이라면 세션에 질문 여부 저장
            if not request.user.is_authenticated:
                request.session["question_asked"] = True

            return JsonResponse({"response": response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)

@login_required
def chat_sessions(request):
    """사용자의 모든 채팅 세션 목록을 가져옴"""
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")
    
    print(f"✅ {request.user.username}의 채팅 세션 개수: {sessions.count()}")  # 디버깅 로그

    session_data = [
        {
            "session_id": session.session_id,
            "latest_message": Message.objects.filter(session=session).order_by("-timestamp").first().content if Message.objects.filter(session=session).exists() else "메시지 없음",
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for session in sessions
    ]

    return JsonResponse({"sessions": session_data})

@login_required
def delete_chat(request, session_id):
    """특정 채팅 세션 삭제"""
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)
        session.delete()
        return JsonResponse({"success": True})
    except ChatSession.DoesNotExist:
        return JsonResponse({"success": False, "error": "세션이 존재하지 않습니다."}, status=404)