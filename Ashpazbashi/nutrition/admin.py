from django.contrib import admin
from .models import Nutrition, IngredientNutrition


@admin.register(Nutrition)
class NutritionAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'calories', 'protein', 'carbohydrates', 'fat']
    search_fields = ['recipe__title']


@admin.register(IngredientNutrition)
class IngredientNutritionAdmin(admin.ModelAdmin):
    list_display = ['ingredient', 'calories_per_100g', 'protein_per_100g', 'carbohydrates_per_100g']
    search_fields = ['ingredient__name']
