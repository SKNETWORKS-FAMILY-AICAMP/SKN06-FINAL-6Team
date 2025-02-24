from django.urls import path
from .views import review_list, review_detail, review_create, review_update, review_delete
from . import views 

urlpatterns = [
    path("", review_list, name="review_list"),
    path("<int:pk>/", review_detail, name="review_detail"),
    path("create/", review_create, name="review_create"),
    path("<int:pk>/edit/", review_update, name="review_update"),
    path("<int:pk>/delete/", review_delete, name="review_delete"),
    path("user/<str:username>/", views.user_reviews, name="user_reviews"),
]
