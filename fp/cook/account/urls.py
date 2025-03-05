from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('find-id/', views.find_id, name='find_id'),
    path('find-password/', views.find_pw, name='find_password'),
    path("send-otp/", views.send_otp_email, name="send_otp_email"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path('mypage/', views.mypage, name='mypage'),
    path('delete/', views.delete_account, name='delete_account'),
]
