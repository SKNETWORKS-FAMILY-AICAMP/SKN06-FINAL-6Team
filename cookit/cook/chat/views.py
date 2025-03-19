import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# 채팅 페이지 렌더링
def chat_view(request):
    if "chat_history" not in request.session or request.GET.get("new_chat"):
        request.session["chat_history"] = [] # 세션 초기화
    return render(request, "chat.html", {"chat_history": request.session["chat_history"]})

FASTAPI_SERVER = "3.39.86.191:9000"

@csrf_exempt
def send_message(request):
    """Django에서 FastAPI로 메시지 전송 (연결 API)"""
    if request.method == "POST":
        data = {
            "message": request.POST.get("message"),
            "session_id": request.POST.get("session_id"),
            "user_id": request.user.id if request.user.is_authenticated else None
        }
        response = requests.post(f"{FASTAPI_SERVER}/chat_api/", json=data)
        return JsonResponse(response.json())
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def chat_history(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return JsonResponse({"success": False, "error": "session_id가 필요합니다."}, status=400)
    fastapi_url = f"{FASTAPI_SERVER}/history/{session_id}/"
    response = requests.get(fastapi_url)
    return JsonResponse(response.json())

@login_required
def chat_sessions(request):
    try:
        response = requests.get(f"{FASTAPI_SERVER}/sessions/")
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
@csrf_exempt
def new_chat(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    try:
        response = requests.post(f"{FASTAPI_SERVER}/new_chat/")
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def delete_chat(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return JsonResponse({"success": False, "error": "session_id가 필요합니다."}, status=400)
    try:
        response = requests.delete(f"{FASTAPI_SERVER}/delete/{session_id}/")
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
def update_retriever(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    try:
        data = request.POST.dict()
        response = requests.post(f"{FASTAPI_SERVER}/update_retriever/", json=data)
        return JsonResponse(response.json())
    except requests.exceptions.RequestException as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

