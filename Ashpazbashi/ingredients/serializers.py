from rest_framework import serializers
from .models import Ingredient, IngredientSubstitute


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'description', 'image', 'unit', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class IngredientSubstituteSerializer(serializers.ModelSerializer):
    original_ingredient = IngredientSerializer(read_only=True)
    substitute_ingredient = IngredientSerializer(read_only=True)
    original_ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='original_ingredient',
        write_only=True
    )
    substitute_ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='substitute_ingredient',
        write_only=True
    )
    
    class Meta:
        model = IngredientSubstitute
        fields = [
            'id', 'original_ingredient', 'substitute_ingredient',
            'original_ingredient_id', 'substitute_ingredient_id',
            'substitution_ratio', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


