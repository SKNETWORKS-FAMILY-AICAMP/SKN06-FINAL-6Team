# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Fridgerecipes(models.Model):
    ids = models.AutoField(primary_key=True)
    id = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    recipe = models.TextField(blank=True, null=True)
    img = models.TextField(blank=True, null=True)
    video = models.TextField(blank=True, null=True)
    ingredients_list = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'FridgeRecipes'


class Funsrecipes(models.Model):
    ids = models.AutoField(primary_key=True)
    id = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    recipe = models.TextField(blank=True, null=True)
    img = models.TextField(blank=True, null=True)
    video = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'FunsRecipes'


class Manrecipes(models.Model):
    ids = models.AutoField(primary_key=True)
    id = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    intro = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    recipe = models.TextField(blank=True, null=True)
    img = models.TextField(blank=True, null=True)
    views = models.TextField(blank=True, null=True)
    video = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    date = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ManRecipes'


class AccountAdminlog(models.Model):
    log_id = models.AutoField(primary_key=True)
    action_type = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    comment = models.ForeignKey('ReviewReviewcomments', models.DO_NOTHING, blank=True, null=True)
    review = models.ForeignKey('ReviewUserreviews', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('AccountUsers', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'account_adminlog'


class AccountUsers(models.Model):
    is_superuser = models.IntegerField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    user_id = models.AutoField(primary_key=True)
    login_id = models.CharField(unique=True, max_length=50)
    provider = models.CharField(max_length=10)
    provider_id = models.CharField(unique=True, max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=255)
    nickname = models.CharField(unique=True, max_length=50)
    birthday = models.DateField()
    points = models.IntegerField()
    status = models.CharField(max_length=12)
    user_photo = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=50)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'account_users'


class AccountUsersGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    users = models.ForeignKey(AccountUsers, models.DO_NOTHING)
    group = models.ForeignKey('AuthGroup', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_users_groups'
        unique_together = (('users', 'group'),)


class AccountUsersUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    users = models.ForeignKey(AccountUsers, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_users_user_permissions'
        unique_together = (('users', 'permission'),)


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class ChatChatsession(models.Model):
    session_id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    user = models.ForeignKey(AccountUsers, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'chat_chatsession'


class ChatHistorychat(models.Model):
    history_id = models.CharField(primary_key=True, max_length=32)
    title = models.CharField(max_length=255)
    messages = models.TextField()
    created_at = models.DateTimeField()
    session = models.ForeignKey(ChatChatsession, models.DO_NOTHING)
    user = models.ForeignKey(AccountUsers, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'chat_historychat'


class ChatUserselectedmenus(models.Model):
    recom_id = models.AutoField(primary_key=True)
    menu_name = models.CharField(max_length=30)
    created_at = models.DateTimeField()
    img_url = models.CharField(max_length=200, blank=True, null=True)
    recipe_id = models.IntegerField(blank=True, null=True)
    source = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(AccountUsers, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'chat_userselectedmenus'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AccountUsers, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class ReviewReviewcomments(models.Model):
    comment_id = models.AutoField(primary_key=True)
    parent_id = models.IntegerField(blank=True, null=True)
    comment_text = models.TextField(blank=True, null=True)
    like_type = models.CharField(max_length=15)
    created_at = models.DateTimeField()
    user = models.ForeignKey(AccountUsers, models.DO_NOTHING)
    review = models.ForeignKey('ReviewUserreviews', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'review_reviewcomments'


class ReviewReviewimages(models.Model):
    image_id = models.AutoField(primary_key=True)
    image_url = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField()
    review = models.ForeignKey('ReviewUserreviews', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'review_reviewimages'


class ReviewUserreviews(models.Model):
    review_id = models.AutoField(primary_key=True)
    review_text = models.TextField()
    rating = models.IntegerField()
    views = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    selected_menu = models.ForeignKey(ChatUserselectedmenus, models.DO_NOTHING)
    user = models.ForeignKey(AccountUsers, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'review_userreviews'
