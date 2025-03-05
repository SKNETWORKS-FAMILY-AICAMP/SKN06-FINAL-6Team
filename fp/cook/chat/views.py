from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from account.models import Users
from account.forms import LoginForm  # forms.py에서 폼 불러오기

def user_login(request):
    form = LoginForm(request.POST or None)  # 폼 생성

    if request.method == "POST" and form.is_valid():  # 폼 검증
        login_id = form.cleaned_data["login_id"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=login_id, password=password)  # ✅ login_id 사용
        if user is not None:
            login(request, user)
            return redirect("home")  # 로그인 성공 시 홈으로 이동
        else:
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")

    return render(request, "account/login.html", {"form": form})  # ✅ 폼을 템플릿에 전달
