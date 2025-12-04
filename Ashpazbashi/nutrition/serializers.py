from rest_framework import serializers
from .models import Nutrition, IngredientNutrition
from ingredients.serializers import IngredientSerializer


class IngredientNutritionSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    
    class Meta:
        model = IngredientNutrition
        fields = [
            'id', 'ingredient', 'calories_per_100g', 'protein_per_100g',
            'carbohydrates_per_100g', 'fat_per_100g', 'fiber_per_100g',
            'sugar_per_100g', 'sodium_per_100g', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NutritionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nutrition
        fields = [
            'id', 'calories', 'protein', 'carbohydrates', 'fat',
            'fiber', 'sugar', 'sodium', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


