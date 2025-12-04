from rest_framework import serializers
from .models import RecipeShare
from recipes.serializers import RecipeListSerializer


class RecipeShareSerializer(serializers.ModelSerializer):
    recipe = RecipeListSerializer(read_only=True)
    
    class Meta:
        model = RecipeShare
        fields = [
            'id', 'recipe', 'share_id', 'created_by',
            'expires_at', 'view_count', 'created_at'
        ]
        read_only_fields = ['id', 'share_id', 'created_by', 'view_count', 'created_at']


