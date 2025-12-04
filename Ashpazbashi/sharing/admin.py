from django.contrib import admin
from .models import RecipeShare


@admin.register(RecipeShare)
class RecipeShareAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'share_id', 'created_by', 'view_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['recipe__title', 'share_id', 'created_by__username']
