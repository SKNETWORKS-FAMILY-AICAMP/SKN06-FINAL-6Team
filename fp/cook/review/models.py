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
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    review_text = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.nickname} - {self.menu.menu_name}"

class UserReviewsImage(models.Model):
    userreviews = models.ForeignKey(UserReviews, related_name="images", on_delete=models.CASCADE)
    image_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

class UserReviewsComment(models.Model):
    userreviews = models.ForeignKey(UserReviews, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    like_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.nickname} - {self.comment_text[:20]}"