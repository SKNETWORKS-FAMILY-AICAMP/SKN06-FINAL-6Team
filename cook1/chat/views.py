import os
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from chat.lcel.lcel import mkch
from chat.utils.memories import mkhisid
from chat.image_detect import detect_ingredients  # YOLO + CLIP 감지 함수

# LLM 체인 초기화
cchain = mkch()

def chat_view(request):
    """채팅 화면을 렌더링하는 뷰"""
    return render(request, "chat.html")

@csrf_exempt
def chat_api(request):
    """사용자의 입력을 받아 AI 응답을 스트리밍 방식으로 반환하는 API"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            query = data.get("query")

            if not user_id or not query:
                return JsonResponse({"error": "user_id와 query를 제공해야 합니다."}, status=400)

            history_id = mkhisid(user_id)

            # AI 응답 스트리밍 함수
            def stream_response():
                response = cchain.stream(
                    {"question": query},
                    config={"configurable": {"user_id": user_id, "history_id": history_id}}
                )

                for chunk_gen in response:
                    for chunk in chunk_gen:
                        yield f"data: {json.dumps({'response': chunk.content})}\n\n"

            return StreamingHttpResponse(
                stream_response(),
                content_type="text/event-stream"
            )


        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "POST 요청만 지원됩니다."}, status=405)

@csrf_exempt
def new_chat(request):
    """새로운 채팅 시작을 위한 뷰"""
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        if not user_id:
            return JsonResponse({"error": "user_id가 필요합니다."}, status=400)
        history_id = mkhisid(user_id)
        return JsonResponse({"message": "새로운 채팅이 시작되었습니다.", "history_id": history_id}, status=200)
