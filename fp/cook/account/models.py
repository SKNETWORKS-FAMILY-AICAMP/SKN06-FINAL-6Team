from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import datetime

class CustomUserManager(BaseUserManager):
    """사용자 계정 생성 매니저"""
    def create_user(self, login_id, email, password=None, **extra_fields):
        if not login_id:
            raise ValueError("로그인 아이디는 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(login_id=login_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(login_id, email, password, **extra_fields)

class Users(AbstractBaseUser, PermissionsMixin):  # ✅ 'CustomUser' → 'Users' 변경
    """사용자 모델"""
    PROVIDER_CHOICES = (
        ('local', 'Local'),
        ('kakao', 'Kakao'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('deactivated', 'Deactivated'),
    )

    user_id = models.AutoField(primary_key=True)  # 기본키
    login_id = models.CharField(max_length=50, unique=True, verbose_name="로그인 ID")
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True, verbose_name="이메일")
    password = models.CharField(max_length=255, null=True, blank=True, verbose_name="비밀번호")
    nickname = models.CharField(max_length=30, unique=True, verbose_name="별명")
    birthdate = models.DateField(null=True, blank=True, verbose_name="생년월일")
    points = models.PositiveIntegerField(default=200, verbose_name="쿠키")  # 기본값 200
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES, default='local', verbose_name="로그인 제공자")
    provider_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="소셜 로그인 ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="회원 상태")
    user_photo = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, verbose_name="프로필 사진")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="가입일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="정보 수정일")
    verification_code = models.CharField(max_length=6, null=True, blank=True, verbose_name="인증 코드")
    verification_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="인증 코드 만료 시간")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100, null=False, blank=True, verbose_name="이름")

    objects = CustomUserManager()

    USERNAME_FIELD = 'login_id'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.login_id

# class EmailVerification(models.Model):
#     user = models.ForeignKey('Users', on_delete=models.CASCADE, null=True, blank=True)
#     email = models.EmailField()  # 이메일 인증을 요청한 이메일
#     verification_code = models.CharField(max_length=6)  # 6자리 인증 코드
#     purpose = models.CharField(max_length=20, choices=[('signup', '회원가입'), ('reset_password', '비밀번호 재설정')])  
#     expires_at = models.DateTimeField(default=timezone.now() + datetime.timedelta(minutes=10))  # 인증번호 만료 시간
#     is_verified = models.BooleanField(default=False)  # 인증 여부

#     created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간

#     def __str__(self):
#         return f"{self.email} - {self.verification_code} ({self.purpose})"

class PointTransaction(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 포인트를 지급받은 사용자
    change_amount = models.IntegerField()  # 포인트 변동량 (+200 같은 값)
    transaction_type = models.CharField(max_length=10, choices=[('earn', '적립'), ('spend', '사용')])
    reason = models.CharField(max_length=255)  # 포인트 지급 이유 (예: "회원가입 보너스")
    created_at = models.DateTimeField(auto_now_add=True)  # 포인트 지급 날짜

    def __str__(self):
        return f"{self.user.login_id} - {self.change_amount} ({self.reason})"
