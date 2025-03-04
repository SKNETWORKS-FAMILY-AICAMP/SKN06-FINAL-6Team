from django.db import models
from django.conf import settings

class Chats(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    chat_id = models.AutoField(primary_key=True)
    question_type = models.CharField(max_length=10, choices=[('text', '텍스트'), ('image', '이미지'), ('tag', '태그'), ('voice', '음성')], default='text')
    question_content = models.TextField()
    response_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class HistoryChat(models.Model):
    history_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    question_content = models.TextField()
    response_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ChatRecommendations(models.Model):
    recommendation_id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(Chats, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    recommended_menu_id = models.IntegerField()
    selected = models.BooleanField(default=False)