from django.db import models
from account.models import Users  # Users 모델 참조

### 1. ChatSession 테이블 (사용자의 대화 흐름을 그룹화)
class ChatSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False)  # ✅ 로그인한 사용자만 가능
    created_at = models.DateTimeField(auto_now_add=True)  # 세션 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 마지막 대화 시간 (최근 대화 순 정렬 가능)

    def __str__(self):
        return f"Session {self.session_id} by {self.user.nickname}"
    
### 2. Chats 테이블 (사용자 질문 및 챗봇 응답 기록)
class Chats(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('tag', 'Tag'),
        ('voice', 'Voice'),
    ]

    chat_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ 비회원 가능
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, null=False)  # 질문 유형
    question_content = models.TextField(null=False)  # 질문 내용
    response_content = models.TextField(null=False)  # 챗봇 응답 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 메시지 전송 시간

    def __str__(self):
        return f"Chat {self.chat_id} by {self.user.nickname if self.user else 'Anonymous'}"

### 3. HistoryChat 테이블 (사용자 채팅 기록 저장)
class HistoryChat(models.Model):
    history_id = models.AutoField(primary_key=True)
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False) 
    title = models.CharField(max_length=255, null=False)  # 첫 번째 질문을 저장할 필드
    created_at = models.DateTimeField(auto_now_add=True)  # 메시지 전송 시간

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
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)  # 채팅 메시지 ID (NOT NULL)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 사용자 ID (NOT NULL)
    id = models.IntegerField(null=False)  # 추천된 메뉴 ID
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=False)  # 출처 (레시피 사이트)
    selected = models.BooleanField(default=False)  # 사용자가 선택한 메뉴 여부

    def __str__(self):
        return f"Recommendation {self.recommendation_id} for {self.user.nickname}"

### 5. UserSelectedMenus 테이블 (사용자가 마이페이지에서 저장한 요리)
class UserSelectedMenus(models.Model):
    SOURCE_CHOICES = [
        ('ManRecipes', 'Man Recipes'),
        ('FridgeRecipes', 'Fridge Recipes'),
        ('FunsRecipes', 'Funs Recipes'),
    ]

    selection_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 사용자 ID (NOT NULL)
    id = models.IntegerField(null=False)  # 선택된 메뉴 ID
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=False)  # 출처
    is_reviewed = models.BooleanField(default=False)  # 사용자가 리뷰 작성했는지 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 저장된 시간

    def __str__(self):
        return f"Selected {self.id} by {self.user.nickname}"

### 6. SavedRecipes 테이블 (사용자가 저장한 레시피)
class SavedRecipes(models.Model):
    SOURCE_CHOICES = [
        ('ManRecipes', 'Man Recipes'),
        ('FridgeRecipes', 'Fridge Recipes'),
        ('FunsRecipes', 'Funs Recipes'),
    ]

    saved_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 사용자 ID (NOT NULL)
    id = models.IntegerField(null=False)  # 저장한 레시피 ID
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=False)  # 출처
    created_at = models.DateTimeField(auto_now_add=True)  # 저장된 시간

    def __str__(self):
        return f"Saved Recipe {self.id} by {self.user.nickname}"

### 7. ManRecipes 테이블 (만개의 레시피)
class ManRecipes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)  # 요리 이름
    intro = models.TextField(null=True, blank=True)  # 요리 한 줄 소개
    info = models.CharField(max_length=255, null=True, blank=True)  # 조리 정보 (몇 인분, 조리 시간, 난이도)
    ingredients = models.TextField(null=False)  # 재료 목록
    recipe = models.TextField(null=False)  # 조리법
    img = models.CharField(max_length=255, null=True, blank=True)  # 요리 이미지 URL
    video = models.CharField(max_length=255, null=True, blank=True)  # 요리 영상 URL
    views = models.IntegerField(default=0)  # 조회수
    date = models.DateTimeField(auto_now_add=True)  # 등록 날짜

    def __str__(self):
        return self.name

### 8. FridgeRecipes 테이블 (냉장고를 부탁해 레시피)
class FridgeRecipes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)  # 요리 이름
    ingredients = models.TextField(null=False)  # 재료 목록
    recipe = models.TextField(null=False)  # 조리법
    img = models.CharField(max_length=255, null=True, blank=True)  # 요리 이미지 URL
    video = models.CharField(max_length=255, null=True, blank=True)  # 요리 영상 URL

    def __str__(self):
        return self.name

### 9. FunsRecipes 테이블 (펀스토랑 레시피)
class FunsRecipes(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)  # 요리 이름
    ingredients = models.TextField(null=False)  # 재료 목록
    recipe = models.TextField(null=False)  # 조리법
    img = models.CharField(max_length=255, null=True, blank=True)  # 요리 이미지 URL
    video = models.CharField(max_length=255, null=True, blank=True)  # 요리 영상 URL

    def __str__(self):
        return self.name