from django.db import models
from account.models import Users  # 사용자 테이블 참조
import uuid

### 1. ChatSession 테이블 (사용자의 대화 흐름을 그룹화)
class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id} by {self.user.nickname}"

### 2. Chats 테이블 (질문 및 챗봇 응답 기록)
class Chats(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('tag', 'Tag'),
        ('voice', 'Voice'),
    ]

    chat_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, null=False)
    question_content = models.TextField(null=False)
    response_content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.chat_id} by {self.user.nickname if self.user else 'Anonymous'}"

### 3. HistoryChat 테이블 (채팅 기록 저장)
class HistoryChat(models.Model):
    history_id = models.AutoField(primary_key=True)
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History {self.history_id} by {self.user.nickname}"

### 4. ChatRecommendations 테이블 (챗봇 추천 요리 저장)
class ChatRecommendations(models.Model):
    SOURCE_CHOICES = [
        ('ManRecipes', 'Man Recipes'),
        ('FridgeRecipes', 'Fridge Recipes'),
        ('FunsRecipes', 'Funs Recipes'),
    ]

    recommendation_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    menu_id = models.IntegerField(null=False, default=0)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=False)
    selected = models.BooleanField(default=False)

    def __str__(self):
        return f"Recommendation {self.recommendation_id} for {self.user.nickname}"
    
class UserSelectedMenus(models.Model):
    user = models.ForeignKey('account.Users', on_delete=models.CASCADE)
    menu_id = models.IntegerField(null=False)
    source = models.CharField(max_length=20, choices=[
        ('ManRecipes', 'Man Recipes'),
        ('FridgeRecipes', 'Fridge Recipes'),
        ('FunsRecipes', 'Funs Recipes'),
    ], null=False)
    created_at = models.DateTimeField(auto_now_add=True)    