from rest_framework import serializers
from .models import RecipeHistory
from recipes.serializers import RecipeListSerializer


class RecipeHistorySerializer(serializers.ModelSerializer):
    recipe = RecipeListSerializer(read_only=True)
    
    class Meta:
        model = RecipeHistory
        fields = ['id', 'recipe', 'viewed_at']
        read_only_fields = ['id', 'viewed_at']


