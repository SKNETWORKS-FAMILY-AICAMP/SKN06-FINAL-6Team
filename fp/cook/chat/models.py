from django.db import models
from django.conf import settings

class Chats(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    chat_id = models.AutoField(primary_key=True)
    question_type = models.CharField(max_length=10, choices=[('text', '텍스트'), ('image', '이미지'), ('tag', '태그'), ('voice', '음성')], default='text')
    question_content = models.TextField()
    response_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class HistoryChat(models.Model):
    history_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    question_content = models.TextField()
    response_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ChatRecommendations(models.Model):
    recommendation_id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(Chats, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    recommended_menu_id = models.IntegerField()
    selected = models.BooleanField(default=False)

class FridgeRecipes(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    ingredients = models.TextField()
    recipe = models.TextField()
    img = models.URLField(null=True, blank=True)
    video = models.URLField(null=True, blank=True)
    ingredients_list = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "menu"

class FunsRecipes(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    ingredients = models.TextField()
    recipe = models.TextField()
    img = models.URLField(null=True, blank=True)
    video = models.URLField(null=True, blank=True)

    class Meta:
        db_table = "fun_menu"

class ManRecipes(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    intro = models.TextField(null=True, blank=True)
    info = models.CharField(max_length=255, null=True, blank=True)
    ingredients = models.JSONField(null=True, blank=True)
    recipe = models.TextField()
    img = models.URLField(null=True, blank=True)
    views = models.IntegerField(default=0)
    video = models.URLField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "processed_data"
