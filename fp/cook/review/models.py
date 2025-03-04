from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Menu(models.Model):
    menu_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.menu_name

class UserReviews(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_id = models.IntegerField()  
    db_source = models.CharField(max_length=20, choices=[("funs", "편스토랑"), ("mans", "만개의 레시피"), ("fridge", "냉장고를 부탁해")])  # ✅ 어떤 DB에서 가져왔는지 저장
    review_text = models.TextField()
    rating = models.IntegerField(default=5.0)
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.nickname} - {self.menu.menu_name}"

class UserReviewsImage(models.Model):
    userreviews = models.ForeignKey(UserReviews, related_name="images", on_delete=models.CASCADE)
    image_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

class UserReviewsComment(models.Model):
    userreviews = models.ForeignKey(UserReviews, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_text = models.TextField(null=True, blank=True)  # 좋아요일 경우 NULL 가능
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    like_type = models.CharField(max_length=20, choices=[('review_like', '리뷰 좋아요'), ('comment', '댓글')], default='comment')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.nickname} - {self.comment_text[:20] if self.comment_text else '좋아요'}"
