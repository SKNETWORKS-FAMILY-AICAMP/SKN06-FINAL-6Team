from django.urls import path
from . import views
from .views import (
    kakao_login, kakao_callback, kakao_logout, kakao_delete_account
)

urlpatterns = [
    # 회원가입 & 로그인 관련
    path('signup/', views.signup, name='signup'),           # 회원가입
    path('login/', views.login_view, name='login'),         # 로그인
    path('logout/', views.logout_view, name='logout'),      # 로그아웃

    # 카카오 로그인 관련 (RESTful 규칙에 맞게 네이밍 수정)
    path("login/kakao/", kakao_login, name="kakao_login"),  
    path("login/kakao/callback/", kakao_callback, name="kakao_callback"),
    path("logout/kakao/", kakao_logout, name="kakao_logout"),
    path("delete/kakao/", kakao_delete_account, name="kakao_delete_account"),  

    # 마이페이지 관련
    path('mypage/', views.mypage, name='mypage'),           # 마이페이지 (회원 정보 수정 가능)
    path('delete-account/', views.delete_account, name='delete_account'),  # 회원 탈퇴

    # 아이디 & 비밀번호 찾기 관련
    path('find-id/', views.find_id, name='find_id'),        # 아이디 찾기
    path('find-pw/', views.find_pw, name='find_pw'),        # 비밀번호 찾기
    path("reset-password/", views.reset_password, name="reset_password"),  # 비밀번호 재설정

    # 이메일 인증
    path("send-email-code/", views.send_otp_email, name="send_email_code"),  # 이메일 인증 코드 전송
    path("verify-email-code/", views.verify_otp, name="verify_email_code"),  # 이메일 인증 확인
]
