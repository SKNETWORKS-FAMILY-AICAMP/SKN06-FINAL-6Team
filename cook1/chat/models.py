from django.db import models
from account.models import Users  # 사용자 테이블 참조
import uuid

### 1. ChatSession 테이블
class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id} by {self.user.nickname}"

### 2. HistoryChat 테이블
class HistoryChat(models.Model):
    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="새로운 질문")
    messages = models.TextField(default="[]")  # JSON 형식으로 저장 가능
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"History {self.history_id} by {self.user.nickname}"

# ### 3. UserSelectedMenus 테이블
# class UserSelectedMenus(models.Model):
#     user = models.ForeignKey('account.Users', on_delete=models.CASCADE)
#     menu_id = models.IntegerField(null=False)
#     source = models.CharField(max_length=20, choices=[
#         ('ManRecipes', 'Man Recipes'),
#         ('FridgeRecipes', 'Fridge Recipes'),
#         ('FunsRecipes', 'Funs Recipes'),
#     ], null=False)
#     created_at = models.DateTimeField(auto_now_add=True) 

#     def __str__(self):
#         return f"{self.user.nickname} - {self.menu_name}"
    
### 3. UserSelectedMenus 테이블
class UserSelectedMenus(models.Model):
    recom_id = models.AutoField(primary_key=True)  # 자동 증가하는 PK
    user = models.ForeignKey('account.Users', on_delete=models.CASCADE)  # 유저 정보
    menu_name = models.CharField(max_length=30, null=False)  # 요리명
    created_at = models.DateTimeField(auto_now_add=True)  # 선택 시간
    img_url = models.URLField(max_length=200, null=True)  # 이미지 URL

    # 나중에 업데이트할 필드 (초기에는 NULL)
    recipe_id = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=20, choices=[
        ('ManRecipes', 'Man Recipes'),
        ('FridgeRecipes', 'Fridge Recipes'),
        ('FunsRecipes', 'Funs Recipes'),
    ], null=True, blank=True)

    def str(self):
        return f"{self.user.nickname} - {self.menu_name} ({self.source})"

# ### 4. SavedRecipes 모델
# class SavedRecipes(models.Model):
#     SOURCE_CHOICES = [
#         ('ManRecipes', 'Man Recipes'),
#         ('FridgeRecipes', 'Fridge Recipes'),
#         ('FunsRecipes', 'Funs Recipes'),
#     ]

#     saved_id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 사용자 ID (NOT NULL)
#     id = models.IntegerField(null=False)  # 저장한 레시피(요리) ID
#     source = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=False)  # db 출처
#     created_at = models.DateTimeField(auto_now_add=True)  # 저장된 시간

#     def str(self):
#         return f"Saved Recipe {self.id} by {self.user.nickname}"