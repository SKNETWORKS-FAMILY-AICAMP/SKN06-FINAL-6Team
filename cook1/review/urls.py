from django.urls import path
from .views import review_list, review_detail, review_create, review_update, user_reviews, review_like, add_comment, delete_comment, add_reply, delete_reply

from . import views 

urlpatterns = [
    path("", review_list, name="review_list"),
    path("<int:pk>/", review_detail, name="review_detail"),
    path("create/", review_create, name="review_create"),
    path("<int:pk>/edit/", review_update, name="review_update"),
    path("user/<str:username>/", views.user_reviews, name="user_reviews"),
    path("review/<int:pk>/like/", views.review_like, name="review_like"),           # 좋아요 기능
    path("review/<int:pk>/comment/", views.add_comment, name="add_comment"),        # 댓글 추가
    path("comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),  # 댓글 삭제
    path("comment/<int:comment_id>/reply/", views.add_reply, name="add_reply"),     # 대댓글 추가
    path("reply/<int:reply_id>/delete/", views.delete_reply, name="delete_reply"),  # 대댓글 삭제
]
