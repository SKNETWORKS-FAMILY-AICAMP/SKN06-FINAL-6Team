from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),      # 회원가입
    path('login/', views.login_view, name='login'),   # 로그인
    path('login/kakao/callback/', views.kakao_login, name='kakao_login'), # 카카오 로그인
    path('logout/', views.logout_view, name='logout'), # 로그아웃
    path('profile/', views.profile, name='profile'),   # 사용자 프로필
    path('find-id/', views.find_id, name='find_id'),  # 아이디 찾기
    path('find-password/', views.find_pw, name='find_pw'),  # 비밀번호 찾기
    path('send-email-code/', views.send_verification_email, name='send_email_code'),  # 이메일 인증번호 전송
    path('verify-email-code/', views.verify_email_code, name='verify_email_code'),  # 이메일 인증 확인
]
