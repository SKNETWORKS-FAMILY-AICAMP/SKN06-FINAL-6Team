from django.shortcuts import render, redirect
from .models import Message
from django.contrib.auth.decorators import login_required

def chat_view(request):
    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            Message.objects.create(user=request.user, content=content)
            return redirect("chat")

    messages = Message.objects.all()
    return render(request, "chat/chat.html", {"messages": messages})
