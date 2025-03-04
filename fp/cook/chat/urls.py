from django.urls import path
from .views import chat_view, chat_api, new_chat, chat_sessions, delete_chat, save_final_recipe

urlpatterns = [
    path("", chat_view, name="chat"),
    path("api/chat/", chat_api, name="chat_api"),
    path("api/new_chat/", new_chat, name="new_chat"),
    path("api/chat_sessions/", chat_sessions, name="chat_sessions"),
    path("api/delete_chat/<int:chat_id>/", delete_chat, name="delete_chat"),
    path("api/save_recipe/", save_final_recipe, name="save_final_recipe"),
]
