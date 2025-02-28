from django.db import models
from django.conf import settings  # Django 설정을 가져오기 위해 추가

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"Session {self.session_id} - {self.user.username if self.user else 'Guest'}"

class Message(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)  # ✅ null 허용
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    response = models.TextField(null=True, blank=True)  # AI 응답 저장
    timestamp = models.DateTimeField(auto_now_add=True)
