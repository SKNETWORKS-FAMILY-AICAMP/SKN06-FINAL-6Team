from django.db import models
from account.models import Users  # Users 모델 참조
from chat.models import UserSelectedMenus # 사용자가 선택한 메뉴 테이블 참조

### 1. UserReviews 테이블 (사용자 리뷰 저장)
class UserReviews(models.Model):
    SOURCE_CHOICES = [
        ('ManRecipes', 'Man Recipes'),
        ('FridgeRecipes', 'Fridge Recipes'),
        ('FunsRecipes', 'Funs Recipes'),
    ]

    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 리뷰 작성자 (NOT NULL)
    selected_menu = models.ForeignKey(UserSelectedMenus, on_delete=models.CASCADE)  # 사용자가 선택한 메뉴와 연결
    review_text = models.TextField(null=False)  # 리뷰 내용
    rating = models.IntegerField(null=False)  # 별점 (1~5)
    views = models.IntegerField(default=0, null=False)  # 조회수 필드 추가 (기본값 0)
    created_at = models.DateTimeField(auto_now_add=True)  # 리뷰 최초 작성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 리뷰 최종 수정 시간

    def __str__(self):
        return f"Review {self.review_id} by {self.user.nickname} (Views: {self.views})"

### 2. ReviewComments 테이블 (리뷰 댓글 및 좋아요)
class ReviewComments(models.Model):
    LIKE_TYPE_CHOICES = [
        ('review_like', 'Review Like'),
        ('comment', 'Comment'),
    ]

    comment_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(UserReviews, on_delete=models.CASCADE)  # 댓글이 달린 리뷰 ID (NOT NULL)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # 작성자 ID 또는 좋아요 누른 사용자 (NOT NULL)
    parent_id = models.IntegerField(null=True, blank=True)  # 대댓글인 경우 부모 댓글 ID (NULL 가능)
    comment_text = models.TextField(null=True, blank=True)  # 댓글 내용 (좋아요일 경우 NULL 가능)
    like_type = models.CharField(max_length=15, choices=LIKE_TYPE_CHOICES, null=False)  # 'review_like' 또는 'comment'
    created_at = models.DateTimeField(auto_now_add=True)  # 작성 시간

    def __str__(self):
        return f"Comment {self.comment_id} on Review {self.review.review_id}"

### 3. ReviewImages 테이블 (리뷰 사진)
class ReviewImages(models.Model):
    image_id = models.AutoField(primary_key=True)
    review = models.ForeignKey(UserReviews, on_delete=models.CASCADE)  # 리뷰 ID (1:N 관계)
    image_url = models.CharField(max_length=255, null=False)  # 업로드된 리뷰 사진 URL
    uploaded_at = models.DateTimeField(auto_now_add=True)  # 업로드 시간

    def __str__(self):
        return f"Image {self.image_id} for Review {self.review.review_id}"
