from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=50, verbose_name="이름", default="")  # 기본값 추가
    nickname = models.CharField(max_length=30, unique=True, verbose_name="별명")
    birthdate = models.DateField(null=True, blank=True, verbose_name="생년월일")
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    point = models.PositiveIntegerField(default=0, verbose_name="쿠키")

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_set",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_set",
        blank=True,
    )
    
    def __str__(self):
        return self.username
