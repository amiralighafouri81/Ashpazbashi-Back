from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Nutrition, IngredientNutrition
from .serializers import NutritionSerializer, IngredientNutritionSerializer
from ingredients.models import Ingredient
from recipes.models import Recipe, RecipeIngredient


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def calculate_nutrition(request):
    """POST /api/nutrition/calculate - Calculate nutrition for a recipe or ingredient list"""
    recipe_id = request.data.get('recipe_id')
    ingredients = request.data.get('ingredients', [])  # List of {ingredient_id, quantity}
    
    if recipe_id:
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            nutrition = Nutrition.objects.filter(recipe=recipe).first()
            if nutrition:
                serializer = NutritionSerializer(nutrition)
                return Response(serializer.data)
            else:
                # Calculate from recipe ingredients
                return calculate_from_recipe(recipe)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    elif ingredients:
        # Calculate from ingredient list
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbohydrates': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0,
        }
        
        for item in ingredients:
            ingredient_id = item.get('ingredient_id')
            quantity = item.get('quantity', '100g')  # Default to 100g
            
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
                nutrition = IngredientNutrition.objects.filter(ingredient=ingredient).first()
                
                if nutrition:
                    # Parse quantity (simplified - assumes format like "100g", "2 cups", etc.)
                    # This is a simplified calculation - in production, you'd need proper unit conversion
                    multiplier = 1.0  # Default multiplier
                    if 'g' in quantity.lower():
                        try:
                            multiplier = float(quantity.lower().replace('g', '')) / 100.0
                        except:
                            multiplier = 1.0
                    
                    total_nutrition['calories'] += float(nutrition.calories_per_100g) * multiplier
                    total_nutrition['protein'] += float(nutrition.protein_per_100g) * multiplier
                    total_nutrition['carbohydrates'] += float(nutrition.carbohydrates_per_100g) * multiplier
                    total_nutrition['fat'] += float(nutrition.fat_per_100g) * multiplier
                    total_nutrition['fiber'] += float(nutrition.fiber_per_100g) * multiplier
                    total_nutrition['sugar'] += float(nutrition.sugar_per_100g) * multiplier
                    total_nutrition['sodium'] += float(nutrition.sodium_per_100g) * multiplier
            except Ingredient.DoesNotExist:
                continue
        
        return Response(total_nutrition)
    
    else:
        return Response(
            {'error': 'Either recipe_id or ingredients list is required'},
            status=status.HTTP_400_BAD_REQUEST
        )


def calculate_from_recipe(recipe):
    """Helper function to calculate nutrition from recipe ingredients"""
    total_nutrition = {
        'calories': 0,
        'protein': 0,
        'carbohydrates': 0,
        'fat': 0,
        'fiber': 0,
        'sugar': 0,
        'sodium': 0,
    }
    
    recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
    for ri in recipe_ingredients:
        nutrition = IngredientNutrition.objects.filter(ingredient=ri.ingredient).first()
        if nutrition:
            # Simplified calculation - assumes quantity is in grams
            multiplier = 1.0
            try:
                if 'g' in ri.quantity.lower():
                    multiplier = float(ri.quantity.lower().replace('g', '')) / 100.0
            except:
                multiplier = 1.0
            
            total_nutrition['calories'] += float(nutrition.calories_per_100g) * multiplier
            total_nutrition['protein'] += float(nutrition.protein_per_100g) * multiplier
            total_nutrition['carbohydrates'] += float(nutrition.carbohydrates_per_100g) * multiplier
            total_nutrition['fat'] += float(nutrition.fat_per_100g) * multiplier
            total_nutrition['fiber'] += float(nutrition.fiber_per_100g) * multiplier
            total_nutrition['sugar'] += float(nutrition.sugar_per_100g) * multiplier
            total_nutrition['sodium'] += float(nutrition.sodium_per_100g) * multiplier
    
    return Response(total_nutrition)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ingredient_nutrition(request, ingredient_id):
    """GET /api/nutrition/ingredients/:id - Get nutrition info for an ingredient"""
    try:
        ingredient = Ingredient.objects.get(id=ingredient_id)
        nutrition = IngredientNutrition.objects.filter(ingredient=ingredient).first()
        if nutrition:
            serializer = IngredientNutritionSerializer(nutrition)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Nutrition information not available for this ingredient'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Ingredient.DoesNotExist:
        return Response(
            {'error': 'Ingredient not found'},
            status=status.HTTP_404_NOT_FOUND
        )
