from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, FindIDForm, PasswordResetForm, FindPWForm, UserUpdateForm, EmailVerificationForm
from .models import Users
from django.core.mail import send_mail
import random
import string
from django.utils.timezone import now, timedelta
import requests
from django.contrib.sessions.models import Session
from django.utils.timezone import now

User = get_user_model()

# 회원가입
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.points = 200  # 기본 포인트 지급
            user.save()
            login(request, user)
            return redirect('profile')
        else:
            print(form.errors)
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

# 로그인
def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('login_id')
        password = request.POST.get('password')

        user = authenticate(request, login_id=login_id, password=password)

        if user is not None:
            login(request, user)
            return redirect('chat')
        else:
            messages.error(request, "아이디 또는 비밀번호가 올바르지 않습니다.")

    return render(request, 'login.html')

# 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')

# 프로필 페이지
@login_required
def profile(request):
    return render(request, 'mypage.html')

# 카카오 API 설정 (REST API 키 & Redirect URI)
REST_API_KEY = ""  
REDIRECT_URI = "http://127.0.0.1:8000/account/login/kakao/callback/"  

def kakao_login(request):
    """카카오 로그인 페이지로 리디렉트 (항상 로그인 창 뜨게 설정)"""
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&prompt=login"
    return redirect(kakao_auth_url)

def kakao_callback(request):
    """ 카카오 로그인 후 사용자 정보를 Django Users 모델과 연동하고 로그인 처리"""
    auth_code = request.GET.get("code")  
    token_url = "https://kauth.kakao.com/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }
    token_response = requests.post(token_url, data=data).json()
    access_token = token_response.get("access_token")

    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info = requests.get(user_info_url, headers=headers).json()

    # 사용자 정보 정리
    kakao_id = user_info.get("id")
    name = user_info["kakao_account"].get("name")
    nickname = user_info["kakao_account"]["profile"]["nickname"]
    email = user_info["kakao_account"].get("email", f"kakao_{kakao_id}@example.com")  # 이메일 없을 경우 기본값 설정
    birthyear = user_info["kakao_account"].get("birthyear")
    birthday = user_info["kakao_account"].get("birthday")  # MMDD 형식
    birthday = f"{birthyear}-{birthday[:2]}-{birthday[2:]}" if birthyear and birthday else None
    
    # Users 모델과 연동
    user, created = Users.objects.get_or_create(
        provider="kakao",
        provider_id=kakao_id,
        defaults={
            "login_id": f"kakao_{kakao_id}",
            "email": email,
            "name": name,
            "nickname": nickname,
            "birthday": birthday,
        }
    )
    # 처음 가입한 유저라면 200 쿠키 지급
    if created:
        user.point = 200  # 첫 카카오 로그인 시 200 쿠키 지급
        user.save()

    # Django 로그인 처리
    login(request, user)

    # 세션에 사용자 정보 저장
    request.session["kakao_id"] = kakao_id
    request.session["kakao_fullname"] = name
    request.session["kakao_nickname"] = nickname
    request.session["kakao_email"] = email
    request.session["kakao_birthday"] = birthday
    request.session["kakao_access_token"] = access_token
    return redirect("chat")  # 로그인 후 chat 화면으로 이동

def kakao_logout(request):
    """로그아웃 (세션 삭제, DB 정보 유지)"""
    if "kakao_id" in request.session:
        print("로그아웃 성공: 세션 삭제 완료!", request.session["kakao_id"])

    request.session.flush()  # 세션 삭제 (DB에는 정보 유지됨)
    
    return redirect("/")  # 로그아웃 후 홈으로 이동

def kakao_delete_account(request):
    """사용자 계정 삭제 (탈퇴) - 로그인한 사용자만 카카오에서 연결 끊기"""
    kakao_id = request.session.get("kakao_id")
    access_token = request.session.get("kakao_access_token")

    if kakao_id and access_token:
        # 1. 카카오 API를 사용하여 개별 사용자 연결 끊기 (unlink)
        unlink_url = "https://kapi.kakao.com/v1/user/unlink"
        headers = {"Authorization": f"Bearer {access_token}"}
        requests.post(unlink_url, headers=headers)

        # 2. DB에서 해당 사용자 정보 삭제
        Users.objects.filter(provider="kakao", provider_id=kakao_id).delete()

    # 3. 탈퇴 처리
    logout(request)
    request.session.clear()
    request.session.flush()
    Session.objects.filter(session_key=request.session.session_key).delete()
    
    response = redirect("login")
    response.delete_cookie("sessionid")  # Django 세션 쿠키 삭제
    response.delete_cookie("csrftoken")  # CSRF 토큰 삭제 (필요하면 추가)

    messages.success(request, "회원 탈퇴가 완료되었습니다.")
    return response

# 아이디 찾기
def find_id(request):
    if request.method == "POST":
        form = FindIDForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]

            try:
                user = Users.objects.get(name=name, email=email)
                return render(request, "find_id.html", {"login_id": user.login_id})
            except Users.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 아이디가 없습니다.")
    else:
        form = FindIDForm()

    return render(request, "find_id.html", {"form": form})

# 비밀번호 찾기
def find_pw(request):
    if request.method == "POST":
        form = FindPWForm(request.POST)
        if form.is_valid():
            login_id = form.cleaned_data["login_id"]
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]

            try:
                user = Users.objects.get(login_id=login_id, name=name, email=email)
                request.session["reset_email"] = email
                return redirect("send_otp_email")
            except Users.DoesNotExist:
                messages.error(request, "입력한 정보와 일치하는 계정이 없습니다.")
    else:
        form = FindPWForm()

    return render(request, "find_pw.html", {"form": form})

def send_otp_email(request):
    """6자리 OTP 생성 및 이메일 전송"""
    email = request.session.get("reset_email")

    if email:
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            messages.error(request, "입력한 이메일과 일치하는 계정이 없습니다.")
            return redirect("find_pw")

        # 6자리 인증번호 생성
        otp = "".join(random.choices(string.digits, k=6))
        
        # Users 테이블의 `verification_code` 필드에 저장
        user.verification_code = otp
        user.verification_expires_at = now() + timedelta(minutes=5)  # 5분 후 만료
        user.save()

        # 이메일 전송
        send_mail(
            "비밀번호 재설정 인증번호",
            f"인증번호: {otp} (5분 내에 입력해주세요.)",
            "cookitcookeat@gmail.com",
            [email],
            fail_silently=False,
        )

        # ✅ 인증번호 입력창을 유지하기 위해 세션 저장
        request.session["show_verification"] = True

        messages.success(request, "인증번호가 이메일로 전송되었습니다! 5분 내에 입력하세요.")
        return redirect("find_pw")
    
    else:
        return redirect("find_pw")

def verify_otp(request):
    """사용자가 입력한 OTP를 검증"""
    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            email = request.session.get("reset_email")

            try:
                user = Users.objects.get(email=email, verification_code=code)
            except Users.DoesNotExist:
                messages.error(request, "잘못된 인증번호입니다.")
                return redirect("find_pw")

            # 인증번호 유효시간 확인
            if user.verification_expires_at and user.verification_expires_at < now():
                messages.error(request, "인증번호가 만료되었습니다. 다시 시도해주세요.")
                return redirect("find_pw")

            # 인증 완료 후, 세션에 비밀번호 재설정 가능 여부 저장
            request.session["is_verified"] = True
            request.session["email_for_password_reset"] = email

            # ✅ 인증 완료 후, 인증번호 입력창 세션 삭제
            request.session.pop("show_verification", None)

            messages.success(request, "인증이 완료되었습니다! 비밀번호를 재설정하세요.")
            return redirect("reset_password")

    else:
        form = EmailVerificationForm()

    return render(request, "verify_email_code.html", {"form": form})

# 비밀번호 재설정
def reset_password(request):
    """비밀번호 재설정"""
    email = request.session.get("email_for_password_reset")
    is_verified = request.session.get("is_verified", False)

    if not email or not is_verified:
        messages.error(request, "인증이 필요합니다.")
        return redirect("find_pw")

    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            
            try:
                user = Users.objects.get(email=email)
            except Users.DoesNotExist:
                messages.error(request, "계정을 찾을 수 없습니다.")
                return redirect("find_pw")

            # 비밀번호 변경
            user.set_password(password)
            user.verification_code = None  # 인증번호 초기화
            user.verification_expires_at = None  # 인증시간 초기화
            user.save()

            # 세션 초기화
            request.session.flush()

            messages.success(request, "비밀번호가 성공적으로 변경되었습니다!")
            return redirect("login")

    else:
        form = PasswordResetForm()

    return render(request, "reset_password.html", {"form": form})

# 마이페이지 (사용자 정보 수정)
@login_required
def mypage(request):
    """사용자 정보 수정 페이지"""
    user = Users.objects.get(pk=request.user.pk)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)  # ✅ 최신 정보 반영
        if form.is_valid():
            form.save()
            messages.success(request, "회원 정보가 수정되었습니다.")
            return redirect('mypage')
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'mypage.html', {'form': form, 'user': user})


# 회원탈퇴
@login_required
def delete_account(request):
    user = request.user
    user.delete()
    messages.success(request, "회원 탈퇴가 완료되었습니다.")
    return redirect('home')
