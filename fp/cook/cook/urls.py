from django.contrib import admin
from django.urls import path, include 
from django.shortcuts import render

def home(request):
    return render(request,"home.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),  
    path("account/", include("account.urls")), 
    path("chat/", include("chat.urls")),
    path("review/", include("review.urls")), 
]
