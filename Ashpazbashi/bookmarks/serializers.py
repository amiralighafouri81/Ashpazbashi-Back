from rest_framework import serializers
from .models import Bookmark
from recipes.models import Recipe
from recipes.serializers import RecipeListSerializer


class BookmarkSerializer(serializers.ModelSerializer):
    recipe = RecipeListSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        source='recipe',
        write_only=True
    )
    
    class Meta:
        model = Bookmark
        fields = ['id', 'recipe', 'recipe_id', 'created_at']
        read_only_fields = ['id', 'created_at']


