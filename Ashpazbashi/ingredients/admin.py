from django.contrib import admin
from .models import Ingredient, IngredientSubstitute


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['unit', 'created_at']


@admin.register(IngredientSubstitute)
class IngredientSubstituteAdmin(admin.ModelAdmin):
    list_display = ['original_ingredient', 'substitute_ingredient', 'substitution_ratio']
    list_filter = ['created_at']
    search_fields = ['original_ingredient__name', 'substitute_ingredient__name']
