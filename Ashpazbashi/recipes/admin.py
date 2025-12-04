from django.contrib import admin
from .models import Recipe, RecipeIngredient, RecipeRating, RecipeGeneration


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'difficulty', 'average_rating', 'views_count', 'is_public', 'created_at']
    list_filter = ['difficulty', 'is_public', 'category', 'created_at']
    search_fields = ['title', 'description', 'author__username']
    inlines = [RecipeIngredientInline]
    filter_horizontal = ['tags', 'dietary_types']


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'ingredient', 'quantity', 'order']
    list_filter = ['recipe', 'ingredient']


@admin.register(RecipeRating)
class RecipeRatingAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['recipe__title', 'user__username']


@admin.register(RecipeGeneration)
class RecipeGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'prompt']
