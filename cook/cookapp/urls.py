from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 예시 URL 패턴
]