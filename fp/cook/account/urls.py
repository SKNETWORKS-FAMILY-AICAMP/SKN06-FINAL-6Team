from django.urls import path
from . import views
from .views import kakao_login, kakao_callback, kakao_logout, kakao_delete_account

urlpatterns = [
    path('signup/', views.signup, name='signup'),          # 회원가입
    path('login/', views.login_view, name='login'),        # 로그인
    path("login/kakao/", kakao_login, name="kakao_login"), # 카카오 로그인
    path("login/kakao/callback/", kakao_callback, name="kakao-callback"),
    path("logout/kakao/", kakao_logout, name="kakao_logout"), # 카카오 로그아웃
    path("delete-account/", kakao_delete_account, name="kakao-delete-account"),  # 카카오 탈퇴
    path('logout/', views.logout_view, name='logout'),     # 로그아웃
    path('profile/', views.profile, name='profile'),       # 사용자 프로필
    path('find-id/', views.find_id, name='find_id'),       # 아이디 찾기
    path('mypage/', views.mypage, name='mypage'),          # 마이페이지
    path('delete/', views.delete_account, name='delete_account'),    # 회원탈퇴
    path("find-pw/", views.find_pw, name="find_pw"),                 # 비번 찾기
    path('find-password/', views.find_pw, name='find_password'), 
    path("send-otp/", views.send_otp_email, name="send_otp_email"),  # OTP 전송
    path("verify-otp/", views.verify_otp, name="verify_otp"),        # OTP 인증
    path("reset-password/", views.reset_password, name="reset_password"), # 비밀번호 재설정
]