from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from chat.models import Chats, ChatSession, HistoryChat
from .chat import mkch  # LLM 연결
from chat.utils.retrievers import load_retriever 
import json
import uuid
import markdown
import re
from django.utils.safestring import mark_safe

# retriever 정의
retriever = load_retriever(True, True, True)

# LLM 체인 생성
llm_chain = mkch()

def chat_view(request):
    """채팅 페이지 렌더링"""
    question_asked = request.session.get("question_asked", False)
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at").first() if request.user.is_authenticated else []
    
    return render(request, "chat.html", {
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

def format_markdown(response):
    """메뉴명만 숫자로 표시하고, 나머지는 일반 텍스트 처리 및 이미지 삽입"""
    lines = response.split("\n")
    formatted_lines = []
    menu_pattern = re.compile(r"^(\d+)\.\s(.*)")  # 메뉴명 패턴 (번호. 제목)
    image_pattern = re.compile(r"!\[.*?\]\((.*?)\)")  # ✅ `![이미지](URL)` 패턴 감지

    for line in lines:
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)  # ✅ `**` 강조 기호 제거

        match = menu_pattern.match(line)
        if match:
            line = f"<h3>{match.group(1)}. {match.group(2)}</h3>"  # ✅ 메뉴명을 <h3>로 변환
        
        # ✅ `사진:`이 포함된 경우 처리
        elif "사진:" in line:
            parts = line.split("사진:")
            if len(parts) > 1:
                image_url = parts[1].strip()
                if image_url and image_url.startswith("http"):  # ✅ URL이 있는 경우에만 처리
                    line = f'<img src="{image_url}" alt="요리 이미지" class="recipe-img" style="width: 250px; height: auto; display: block; margin: 10px auto;">'
        
        # ✅ `![이미지](URL)` 패턴을 감지하여 변환
        line = image_pattern.sub(r'<img src="\1" alt="요리 이미지" class="recipe-img" style="width: 250px; height: auto; display: block; margin: 10px auto;">', line)

        formatted_lines.append(line)

    return markdown.markdown("\n".join(formatted_lines), extensions=["extra"])

def chat_api(request):
    """사용자의 입력을 받아 LLM을 호출하고 응답을 반환하는 API"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"error": "메시지를 입력해주세요."}, status=400)

            if not request.user.is_authenticated and request.session.get("question_asked", False):
                return JsonResponse({"error": "비회원 사용자는 한 번만 질문할 수 있습니다."}, status=403)

            if request.user.is_authenticated:
                if request.user.points < 10:
                    return JsonResponse({"error": "쿠키가 부족하여 채팅을 보낼 수 없습니다."}, status=403)
                request.user.points -= 10
                request.user.save()

            # ✅ 현재 세션 ID 가져오기
            session_id = data.get("session_id")
            if session_id:
                chat_session = ChatSession.objects.filter(session_id=session_id).first()
            else:
                chat_session = ChatSession.objects.filter(user=request.user).order_by("-created_at").first()

            if not chat_session:
                chat_session = ChatSession.objects.create(user=request.user, session_id=str(uuid.uuid4()))

            # ✅ 이전 대화 내용 불러오기 (히스토리 포함)
            previous_chats = Chats.objects.filter(session=chat_session).order_by("created_at")
            chat_history = [{"question": chat.question_content, "response": chat.response_content} for chat in previous_chats]

            # ✅ `retriever.invoke()` 실행 후 값이 없으면 빈 리스트 반환
            context_data = retriever.invoke(user_message) if retriever else []
            if not context_data:
                print("⚠️ context_data가 비어 있습니다. retriever 설정을 확인하세요!")
                context_data = []  # 빈 리스트 반환하여 KeyError 방지

            # ✅ LLM 요청 전 디버깅 로그 출력
            print("🔍 사용자 질문:", user_message)
            print("📝 전달할 대화 기록:", chat_history)
            print("📢 전달할 context_data:", context_data)

            # ✅ LLM 요청 시 대화 이력을 함께 전달
            response = llm_chain.invoke(
                input={  # 첫 번째 인자: `input`에 `question`, `history`, `contents` 전달
                    "question": user_message,
                    "history": chat_history,  # 🔹 대화 이력 추가
                    "contents": context_data  # 🔹 retriever 결과 추가
                },
                config={  # 두 번째 인자: `config`에 설정 값 전달
                    "configurable": {
                        "history_id": str(chat_session.session_id),
                        "user_id": str(request.user.pk) if request.user.is_authenticated else "guest"
                    }
                }
            )
            print("🔍 LLM Response:", response)

            formatted_response = format_markdown(response)  # ✅ 마크다운 변환 적용

            # ✅ 데이터베이스에 저장
            Chats.objects.create(
                session=chat_session,
                user=request.user if request.user.is_authenticated else None,
                question_content=user_message,
                response_content=formatted_response
            )

            if not request.user.is_authenticated:
                request.session["question_asked"] = True

            return JsonResponse({"response": mark_safe(formatted_response)})

        except json.JSONDecodeError:
            return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)

@login_required
def chat_sessions(request):
    """사용자의 모든 채팅 세션 목록을 가져옴 (요약 포함)"""
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")

    session_data = []
    for session in sessions:
        history = HistoryChat.objects.filter(session=session).first()
        title = history.title if history else "대화 기록 없음"
        
        # ✅ 채팅 요약 (첫 번째 메시지 가져오기)
        first_chat = Chats.objects.filter(session=session).order_by("created_at").first()
        summary = first_chat.question_content[:30] if first_chat else "대화 요약 없음"
        
        session_data.append({
            "session_id": str(session.session_id),
            "title": title,
            "summary": summary,
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return JsonResponse({"sessions": session_data})
    
@login_required
def chat_history(request, session_id):
    """특정 세션의 채팅 내역을 불러옴"""
    try:
        chat_session = ChatSession.objects.get(session_id=str(session_id))
    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "채팅 세션을 찾을 수 없습니다."}, status=404)
    
    messages = Chats.objects.filter(session=chat_session).order_by("created_at")

    message_list = []
    for msg in messages:
        message_list.append({
            "content": markdown.markdown(msg.question_content),
            "sender": "User",
            "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
        if msg.response_content:
            message_list.append({
                "content": markdown.markdown(msg.response_content),
                "sender": "AI",
                "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

    return JsonResponse({
        "session_id": session_id,
        "messages": message_list
    })

@login_required
def delete_chat(request, session_id):
    """특정 채팅 세션 삭제"""
    try:
        session = ChatSession.objects.filter(session_id=session_id, user=request.user).first()
        session.delete()
        return JsonResponse({"success": True})
    except ChatSession.DoesNotExist:
        return JsonResponse({"success": False, "error": "세션이 존재하지 않습니다."}, status=404)
