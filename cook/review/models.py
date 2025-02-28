from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Review(models.Model):
    """기존 리뷰 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 작성자
    menu_name = models.CharField(max_length=200)  # 메뉴명
    content = models.TextField()  # 리뷰 내용
    rating = models.FloatField(default=5.0)  # 별점 (0.5 ~ 5.0)
    views = models.PositiveIntegerField(default=0)  # 조회수
    created_at = models.DateTimeField(auto_now_add=True)  # 작성 날짜
    updated_at = models.DateTimeField(auto_now=True)  # 수정 날짜

    def __str__(self):
        return self.menu_name

# 여러 개의 이미지 저장 가능하도록 모델 추가
class ReviewImage(models.Model):
    review = models.ForeignKey(Review, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="review_images/")


class ReviewComment(models.Model):
    """댓글 모델"""
    review = models.ForeignKey(Review, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

class Reply(models.Model):
    """대댓글 모델"""
    comment = models.ForeignKey(ReviewComment, on_delete=models.CASCADE, related_name="replies")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ReviewLike(models.Model):
    """좋아요 모델"""
    review = models.ForeignKey(Review, related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("review", "user")  # 한 사용자가 한 리뷰에 