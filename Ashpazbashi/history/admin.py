from django.contrib import admin
from .models import RecipeHistory


@admin.register(RecipeHistory)
class RecipeHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username', 'recipe__title']
