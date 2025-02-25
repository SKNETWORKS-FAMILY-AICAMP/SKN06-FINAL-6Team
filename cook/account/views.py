from django.shortcuts import render, redirect, get_object_or_404
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
from .forms import CustomUserCreationForm, FindIDForm, FindPWForm, EmailVerificationForm, UserUpdateForm, PasswordResetForm

User = get_user_model()


# ✅ 회원가입
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/signup.html', {'form': form})


# ✅ 로그인
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('chat')
    else:
        form = AuthenticationForm()
    return render(request, 'account/login.html', {'form': form})


# ✅ 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')


# ✅ 프로필 (로그인된 사용자만 접근 가능)
@login_required
def profile(request):
    return render(request, 'account/mypage.html')


# ✅ 카카오 로그인
def kakao_login(request):
    client_id = 'YOUR_KAKAO_REST_API_KEY'
    redirect_uri = 'http://127.0.0.1:8000/account/login/kakao/callback/'
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(kakao_auth_url)


# ✅ 카카오 로그인 콜백
def kakao_callback(request):
    code = request.GET.get('code')
    client_id = 'YOUR_KAKAO_REST_API_KEY'
    redirect_uri = 'http://127.0.0.1:8000/account/login/kakao/callback/'

    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': code
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    user_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {token_json['access_token']}"}
    user_response = requests.get(user_url, headers=headers)
    user_json = user_response.json()

    request.session['kakao_id'] = user_json['id']
    request.session['kakao_nickname'] = user_json['properties']['nickname']

    return redirect('profile')


# ✅ 아이디 찾기 (이름 + 이메일)
def find_id(request):
    if request.method == "POST":
        form = FindIDForm(request.POST)
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


# ✅ 비밀번호 찾기 (아이디 + 이름 + 이메일)
def find_pw(request):
    if request.method == "POST":
        form = FindPWForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            full_name = form.cleaned_data["full_name"]
            email = form.cleaned_data["email"]

            try:
                user = User.objects.get(username=username, full_name=full_name, email=email)
                request.session["reset_email"] = email
                return redirect("send_otp_email")
            except User.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 계정이 없습니다.")
    else:
        form = FindPWForm()

    return render(request, "account/find_pw.html", {"form": form})


# ✅ OTP 이메일 전송
def send_otp_email(request):
    """6자리 OTP 생성 및 이메일 전송"""
    email = request.session.get("reset_email")

    if email:
        otp = "".join(random.choices(string.digits, k=6))
        request.session["otp_code"] = str(otp)
        request.session["is_verified"] = False
        # request.session.set_expiry(5000)  # 세션 유효시간

        # 이메일 전송
        send_mail(
            "비밀번호 재설정 인증번호",
            f"인증번호: {otp} (5분 내에 입력해주세요.)",
            "jhw7246@gmail.com",
            [email],
            fail_silently=False,
        )

        return render(request, "account/send_email_code.html", {"email": email})
    else:
        return redirect("find_pw")


# ✅ OTP 인증 확인
def verify_otp(request):
    """사용자가 입력한 OTP를 검증"""
    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]

            # 세션에서 인증번호 확인
            otp_code = request.session.get("otp_code")
            reset_email = request.session.get("reset_email")

            if otp_code and reset_email and str(code) == str(otp_code):
                request.session["is_verified"] = True
                request.session["email_for_password_reset"] = reset_email
                messages.success(request, "인증이 완료되었습니다! 비밀번호를 재설정하세요.")
                return redirect("reset_password")
            else:
                messages.error(request, "인증번호가 일치하지 않거나 만료되었습니다.")
        else:
            print("폼 오류:", form.errors)
            messages.error(request, "유효하지 않은 입력입니다.")
    else:
        form = EmailVerificationForm()

    return render(request, "account/verify_email_code.html", {"form": form})


def reset_password(request):
    """비밀번호 재설정 페이지"""
    email = request.session.get("email_for_password_reset")
    is_verified = request.session.get("is_verified", False)

    if not email or not is_verified:
        messages.error(request, "인증이 필요합니다.")
        return redirect("find_pw")

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()

            # ✅ 세션 초기화
            request.session.flush()

            messages.success(request, "비밀번호가 성공적으로 변경되었습니다!")
            return redirect("login")
        else:
            print("폼 오류:", form.errors)
            messages.error(request, "유효하지 않은 입력입니다.")
    else:
        form = PasswordResetForm()

    return render(request, "account/reset_password.html", {"form": form})


# ✅ 마이페이지 (사용자 정보 수정)
@login_required
def mypage(request):
    """사용자 정보 수정 페이지"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "회원 정보가 수정되었습니다.")
            return redirect('mypage')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'account/mypage.html', {'form': form})


# ✅ 회원탈퇴
@login_required
def delete_account(request):
    """회원탈퇴 기능"""
    user = request.user
    user.delete()
    messages.success(request, "회원 탈퇴가 완료되었습니다.")
    return redirect('home')
