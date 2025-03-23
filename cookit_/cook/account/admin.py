from django.contrib import admin
from .models import AdminLog

@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'user', 'review', 'comment', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('user__nickname', 'review__review_text')
