from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import requests
import random
import string
from django.conf import settings
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from .forms import CustomUserCreationForm, FindIDForm, FindPWForm, EmailVerificationForm, UserUpdateForm, PasswordResetForm
from .models import Users, EmailVerification, PointTransaction
from django.db import transaction

User = get_user_model()

# 회원가입 (200 쿠키 지급 반영)
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)  # 저장을 보류
                user.points = 200  # 회원가입 시 200 쿠키 지급
                user.save()

                # 포인트 지급 내역 추가
                PointTransaction.objects.create(
                    user=user,
                    change_amount=200,
                    transaction_type='earn',
                    reason='회원가입 보너스'
                )

                login(request, user)
                return redirect('mypage')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/signup.html', {'form': form})


# 로그인
def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get("login_id")
        password = request.POST.get("password")
        user = authenticate(request, login_id=login_id, password=password)
        if user:
            login(request, user)
            return redirect('chat')
        else:
            messages.error(request, "아이디 또는 비밀번호가 일치하지 않습니다.")
    return render(request, 'account/login.html')


# 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')


# 프로필 (마이페이지)
@login_required
def mypage(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "회원 정보가 수정되었습니다.")
            return redirect('mypage')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'account/mypage.html', {'form': form})


# 아이디 찾기 (이름 + 이메일)
def find_id(request):
    if request.method == "POST":
        form = FindIDForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            email = form.cleaned_data["email"]

            try:
                user = Users.objects.get(full_name=full_name, email=email)
                return render(request, "account/find_id.html", {"login_id": user.login_id})
            except Users.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 아이디가 없습니다.")
    else:
        form = FindIDForm()

    return render(request, "account/find_id.html", {"form": form})


# 비밀번호 찾기 (아이디 + 이메일)
def find_pw(request):
    if request.method == "POST":
        form = FindPWForm(request.POST)
        if form.is_valid():
            login_id = form.cleaned_data["login_id"]
            email = form.cleaned_data["email"]

            try:
                user = Users.objects.get(login_id=login_id, email=email)

                # 인증 코드 생성 및 저장
                verification_code = "".join(random.choices(string.digits, k=6))
                EmailVerification.objects.create(
                    user=user,
                    email=email,
                    verification_code=verification_code,
                    purpose="reset_password"
                )

                # 이메일 전송
                send_mail(
                    "비밀번호 재설정 인증번호",
                    f"인증번호: {verification_code} (10분 내 입력)",
                    "noreply@cookit.com",
                    [email],
                    fail_silently=False
                )

                request.session["reset_email"] = email
                return redirect("verify_email_code")
            except Users.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 계정이 없습니다.")
    else:
        form = FindPWForm()

    return render(request, "account/find_pw.html", {"form": form})


# 비밀번호 재설정
def reset_password(request):
    email = request.session.get("reset_email")

    if not email:
        messages.error(request, "비밀번호 재설정을 위해 먼저 인증하세요.")
        return redirect("find_pw")

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            user = Users.objects.get(email=email)
            user.set_password(password)
            user.save()
            request.session.flush()
            messages.success(request, "비밀번호가 성공적으로 변경되었습니다!")
            return redirect("login")

    return render(request, "account/reset_password.html")


# 카카오 로그인
def kakao_login(request):
    REST_API_KEY = settings.KAKAO_REST_API_KEY
    REDIRECT_URI = settings.KAKAO_REDIRECT_URI
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&prompt=login"
    return redirect(kakao_auth_url)


def kakao_callback(request):
    """카카오 로그인 후 사용자 정보를 Users 모델과 연동"""
    auth_code = request.GET.get("code")
    token_url = "https://kauth.kakao.com/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_REST_API_KEY,
        "redirect_uri": settings.KAKAO_REDIRECT_URI,
        "code": auth_code
    }
    token_response = requests.post(token_url, data=data).json()
    access_token = token_response.get("access_token")

    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info = requests.get(user_info_url, headers=headers).json()

    kakao_id = user_info.get("id")
    email = user_info["kakao_account"].get("email", f"kakao_{kakao_id}@example.com")
    nickname = user_info["kakao_account"]["profile"]["nickname"]

    user, created = Users.objects.get_or_create(
        provider="kakao",
        provider_id=kakao_id,
        defaults={"email": email, "nickname": nickname}
    )

    if created:
        user.points = 200
        user.save()

    login(request, user)
    return redirect("chat")

def kakao_logout(request):
    """ 카카오 로그아웃 (세션 삭제, DB 정보 유지)"""
    if "kakao_id" in request.session:
        print( "로그아웃 성공: 세션 삭제 완료!", request.session["kakao_id"])
    
    request.session.flush()  # 세션 삭제 (DB에는 정보 유지됨)
    
    return redirect("/")  # 로그아웃 후 홈으로 이동

import requests

def kakao_delete_account(request):
    """카카오 계정 삭제 (회원탈퇴)"""
    kakao_id = request.session.get("kakao_id")
    access_token = request.session.get("kakao_access_token")  # 로그인한 사용자의 access_token 사용

    if kakao_id and access_token:
        # 카카오 API를 사용하여 개별 사용자 연결 끊기 (unlink)
        unlink_url = "https://kapi.kakao.com/v1/user/unlink"
        headers = {"Authorization": f"Bearer {access_token}"}  # 사용자 access_token 사용
        requests.post(unlink_url, headers=headers)

        # DB에서 해당 사용자 정보 삭제
        Users.objects.filter(provider_id=kakao_id).delete()

    # 로그아웃 처리 (세션에서 사용자 정보 제거)
    logout(request)
    request.session.flush()

    messages.success(request, "카카오 계정이 성공적으로 삭제되었습니다.")
    return redirect("login")

def send_otp_email(request):
    """이이메일로 6자리 OTP 인증번호 전송"""
    email = request.session.get("reset_email")

    if email:
        otp = "".join(random.choices(string.digits, k=6))
        request.session["otp_code"] = str(otp)
        request.session["is_verified"] = False

        # 이메일 전송
        send_mail(
            "비밀번호 재설정 인증번호",
            f"인증번호: {otp} (5분 내에 입력해주세요.)",
            "cookitcookeat@gmail.com",
            [email],
            fail_silently=False,
        )

        # EmailVerification 모델에 인증 코드 저장
        verification = EmailVerification.objects.create(
            email=email,
            verification_code=otp,
            purpose="reset_password",  # 비밀번호 재설정용
            expires_at=timezone.now() + datetime.timedelta(minutes=10)  # 10분 뒤 만료
        )

        return render(request, "account/send_email_code.html", {"email": email})
    else:
        return redirect("find_pw")


def verify_otp(request):
    """사용자가 입력한 OTP 인증번호 검증"""
    if request.method == "POST":
        code = request.POST.get("code")

        # 세션에서 인증번호 확인
        otp_code = request.session.get("otp_code")
        reset_email = request.session.get("reset_email")

        if otp_code and reset_email and str(code) == str(otp_code):
            # 인증이 성공하면 세션에 정보 저장
            request.session["is_verified"] = True
            request.session["email_for_password_reset"] = reset_email
            messages.success(request, "인증이 완료되었습니다! 비밀번호를 재설정하세요.")
            return redirect("reset_password")
        else:
            # 인증 실패 메시지
            messages.error(request, "인증번호가 일치하지 않거나 만료되었습니다.")
    
    return render(request, "account/verify_email_code.html")

# 회원탈퇴
@login_required
def delete_account(request):
    user = request.user
    user.delete()
    messages.success(request, "회원 탈퇴가 완료되었습니다.")
    return redirect('home')
