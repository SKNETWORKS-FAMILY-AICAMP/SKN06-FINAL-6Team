from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
import random
import string
from django.conf import settings
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from .forms import CustomUserCreationForm, FindIDForm, FindPWForm, EmailVerificationForm  # ✅ 올바른 폼 이름 사용

User = get_user_model()

# 회원가입
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 회원가입 후 자동 로그인
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/signup.html', {'form': form})

# 로그인
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')  # 로그인 후 프로필 페이지로 이동
    else:
        form = AuthenticationForm()
    return render(request, 'account/login.html', {'form': form})

# 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')

# 프로필 (로그인된 사용자만 접근 가능)
@login_required
def profile(request):
    return render(request, 'account/profile.html')

# 카카오 로그인
def kakao_login(request):
    client_id = 'YOUR_KAKAO_REST_API_KEY'  # 카카오 REST API 키
    redirect_uri = 'http://127.0.0.1:8000/account/login/kakao/callback/'
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(kakao_auth_url)

# 카카오 로그인 콜백
def kakao_callback(request):
    code = request.GET.get('code')
    client_id = 'YOUR_KAKAO_REST_API_KEY'
    redirect_uri = 'http://127.0.0.1:8000/account/login/kakao/callback/'

    # 액세스 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': code
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    # 사용자 정보 요청
    user_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {token_json['access_token']}"}
    user_response = requests.get(user_url, headers=headers)
    user_json = user_response.json()

    # 세션에 사용자 정보 저장
    request.session['kakao_id'] = user_json['id']
    request.session['kakao_nickname'] = user_json['properties']['nickname']

    return redirect('profile')

# 아이디 찾기 (이름 + 이메일)
def find_id(request):
    if request.method == "POST":
        form = FindIDForm(request.POST)  # ✅ FindUsernameForm → FindIDForm 변경
        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            email = form.cleaned_data["email"]
            
            try:
                user = User.objects.get(full_name=full_name, email=email)
                return render(request, "account/find_id.html", {"username": user.username})
            except User.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 아이디가 없습니다.")
    
    else:
        form = FindIDForm()

    return render(request, "account/find_id.html", {"form": form})

# 비밀번호 찾기 (아이디 + 이름 + 이메일)
def find_pw(request):
    if request.method == "POST":
        form = FindPWForm(request.POST)  # ✅ FindPasswordForm → FindPWForm 변경
        if form.is_valid():
            username = form.cleaned_data["username"]
            full_name = form.cleaned_data["full_name"]
            email = form.cleaned_data["email"]
            
            try:
                user = User.objects.get(username=username, full_name=full_name, email=email)
                return redirect("send_email_code")  # 인증번호 전송 페이지로 이동
            except User.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 계정이 없습니다.")
    
    else:
        form = FindPWForm()

    return render(request, "account/find_pw.html", {"form": form})
# 이메일 인증번호 생성 & 전송
def send_verification_email(request):
    if request.method == "POST":
        email = request.POST.get("email")

        # 6자리 랜덤 코드 생성
        verification_code = "".join(random.choices(string.digits, k=6))

        # 세션에 저장 (임시)
        request.session["verification_code"] = verification_code
        request.session["email_for_verification"] = email

        # 이메일 발송
        send_mail(
            "비밀번호 찾기 인증번호",
            f"인증번호: {verification_code}",
            "noreply@yourwebsite.com",
            [email],
            fail_silently=False,
        )
        return JsonResponse({"message": "이메일로 인증번호를 전송했습니다!"})

    return render(request, "account/send_email_code.html")

# 이메일 인증 확인
def verify_email_code(request):
    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            code = form.cleaned_data["code"]

            # 세션에서 인증번호 확인
            if (
                "verification_code" in request.session
                and "email_for_verification" in request.session
                and request.session["verification_code"] == code
                and request.session["email_for_verification"] == email
            ):
                messages.success(request, "인증이 완료되었습니다!")
                return redirect("reset_password")  # 비밀번호 재설정 페이지로 이동
            else:
                messages.error(request, "인증번호가 일치하지 않습니다.")
    
    else:
        form = EmailVerificationForm()

    return render(request, "account/verify_email_code.html", {"form": form})
