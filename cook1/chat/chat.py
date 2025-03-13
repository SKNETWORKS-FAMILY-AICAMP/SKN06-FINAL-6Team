import os
import json
from django.http import JsonResponse
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
    """ Django에서 AI 챗봇 API로 사용할 수 있는 View 함수 """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            query = data.get("query")

            if not user_id or not query:
                return JsonResponse({"error": "user_id와 query를 제공해야 합니다."}, status=400, json_dumps_params={'ensure_ascii': False})

            history_id = mkhisid(user_id)

            # 이미지 감지 및 텍스트 추출
            input_parts = query.split()
            detected_ingredients = set()
            text_input = []

            for part in input_parts:
                if os.path.exists(part) and part.lower().endswith((".jpg", ".jpeg", ".png")):
                    detected_ingredients.update(detect_ingredients(part))
                else:
                    text_input.append(part)

            # 최종 Query 구성
            detected_ingredients = sorted(detected_ingredients)
            combined_query = " ".join(text_input)
            query_with_ingredients = f"{combined_query} 감지된 재료: {', '.join(detected_ingredients)}" if detected_ingredients else combined_query

            # 🔥 LLM에 질문을 전달하여 요리 추천 받기
            res = cchain.invoke(
                {"question": query_with_ingredients},
                config={"configurable": {"user_id": user_id, "history_id": history_id}}
            )

            return JsonResponse({"response": res}, status=200, json_dumps_params={'ensure_ascii': False})
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500, json_dumps_params={'ensure_ascii': False})

    return JsonResponse({"error": "POST 요청만 지원됩니다."}, status=405, json_dumps_params={'ensure_ascii': False})

@csrf_exempt
def new_chat(request):
    """새로운 채팅 시작을 위한 뷰"""
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        if not user_id:
            return JsonResponse({"error": "user_id가 필요합니다."}, status=400)
        history_id = mkhisid(user_id)
        return JsonResponse({"message": "새로운 채팅이 시작되었습니다.", "history_id": history_id}, status=200)