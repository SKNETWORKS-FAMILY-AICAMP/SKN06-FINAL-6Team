from django.urls import path
from .views import (
    userreviews_list, userreviews_detail, userreviews_create, userreviews_update,
    review_like  # ✅ 추가된 뷰 함수 등록
)

urlpatterns = [
    path("", userreviews_list, name="userreviews_list"),
    path("<int:pk>/", userreviews_detail, name="userreviews_detail"),
    path("create/", userreviews_create, name="userreviews_create"),
    path("<int:pk>/edit/", userreviews_update, name="userreviews_update"),
    path("review/<int:pk>/like/", review_like, name="review_like"),  # ✅ 좋아요 기능 추가
]
