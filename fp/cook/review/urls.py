from django.urls import path
from .views import userreviews_list, userreviews_detail, userreviews_create, userreviews_update
from . import views 

urlpatterns = [
    path("", userreviews_list, name="userreviews_list"),
    path("<int:pk>/", userreviews_detail, name="userreviews_detail"),
    path("create/", userreviews_create, name="userreviews_create"),
    path("<int:pk>/edit/", userreviews_update, name="userreviews_update"),
    path("comment/<int:pk>/like/", views.comment_like, name="comment_like"),
    path("userreviews/<int:pk>/comment/", views.add_comment, name="add_comment"),        # 댓글 추가
    path("comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),  # 댓글 삭제
    path("comment/<int:comment_id>/reply/", views.add_reply, name="add_reply"),     # 대댓글 추가
    path("reply/<int:reply_id>/delete/", views.delete_reply, name="delete_reply"),  # 대댓글 삭제
]