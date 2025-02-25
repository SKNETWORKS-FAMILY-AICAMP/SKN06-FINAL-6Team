from django.db import models
from django.conf import settings  # Django 설정을 가져오기 위해 추가

class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 수정된 부분
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
