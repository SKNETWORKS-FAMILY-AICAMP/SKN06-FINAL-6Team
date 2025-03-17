from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser

### 1. Users 테이블 (사용자 정보)
class Users(AbstractUser):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deactivated', 'Deactivated'),
    ]

    PROVIDER_CHOICES = [
        ('local', 'Local'),
        ('kakao', 'Kakao'),
    ]

    user_id = models.AutoField(primary_key=True)
    login_id = models.CharField(max_length=50, unique=True, null=False)  # local 전용 로그인 ID
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES, default='local', null=False)
    provider_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # 소셜 로그인 ID (NULL 허용)
    email = models.EmailField(max_length=100, unique=True, null=False)  # 이메일 (NOT NULL)
    password = models.CharField(max_length=255, null=False)  # 비밀번호 (NOT NULL, 해싱 저장)
    nickname = models.CharField(max_length=50, unique=True, null=False)  # 별명 (NOT NULL)
    birthday = models.DateField(null=False)  # 생년월일 (NOT NULL)
    points = models.IntegerField(default=200, null=False)  # 기본 포인트 200
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active', null=False)  # 계정 상태
    user_photo = models.ImageField(upload_to="user_photo/", blank=True, null=True)
    name = models.CharField(max_length=50, null=False)  # 사용자 본명 (NOT NULL)
    email_verified_at = models.DateTimeField(null=True, blank=True)  # 이메일 인증 완료 시간 (NULL 가능)
    verification_code = models.CharField(max_length=6, null=True, blank=True)  # 이메일 인증번호 (NULL 가능)
    verification_expires_at = models.DateTimeField(null=True, blank=True)  # 인증번호 만료 시간 (NULL 가능)
    created_at = models.DateTimeField(auto_now_add=True)  # 계정 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 계정 정보 수정 시간
    last_login = models.DateTimeField(default=now, null=True, blank=True)
    
    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS = ["email", "password", "nickname", "birthday", "name"]

    username=None
    
    def __str__(self):
        return self.nickname

### 2. LoginSessions 테이블 (로그인 세션 관리)
class LoginSessions(models.Model):
    session_id = models.CharField(max_length=255, primary_key=True)  # 세션 고유 ID
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False)  # 로그인한 사용자 (NOT NULL)
    created_at = models.DateTimeField(auto_now_add=True)  # 로그인 시간
    expired_at = models.DateTimeField(null=True, blank=True)  # 세션 만료 시간 (NULL 가능)

    def __str__(self):
        return f"Session {self.session_id} for {self.user.nickname}"

### 3. PointTransaction 테이블 (포인트 변동 내역)
class PointTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('earn', 'Earn'),
        ('spend', 'Spend'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, null=False)  # 포인트 변동 사용자 (NOT NULL)
    change_amount = models.IntegerField(null=False)  # 포인트 변경 값 (NOT NULL)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, null=False)  # 적립/사용 구분 (NOT NULL)
    reason = models.CharField(max_length=255, null=False)  # 포인트 변동 사유 (NOT NULL)
    updated_at = models.DateTimeField(auto_now_add=True)  # 포인트 변경 시간

    def __str__(self):
        return f"{self.user.nickname} - {self.transaction_type} {self.change_amount} points"

### 4. AdminLogs 테이블 (관리자 활동 기록)
class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('modify_points', 'Modify Points'),
        ('delete_review', 'Delete Review'),
        ('ban_user', 'Ban User'),
    ]

    log_id = models.AutoField(primary_key=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, null=False)  # 관리자 수행 작업 (NOT NULL)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)  # 관리자 처리 사용자 (NULL 가능)
    review = models.ForeignKey('review.UserReviews', on_delete=models.SET_NULL, null=True, blank=True)  # 처리된 리뷰 (NULL 가능)
    comment = models.ForeignKey('review.ReviewComments', on_delete=models.SET_NULL, null=True, blank=True)  # 처리된 댓글 (NULL 가능)
    created_at = models.DateTimeField(auto_now_add=True)  # 작업 수행 시간 (NOT NULL)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.created_at}"
