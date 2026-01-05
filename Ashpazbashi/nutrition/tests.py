from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Nutrition, IngredientNutrition
from recipes.models import Recipe, RecipeIngredient
from ingredients.models import Ingredient
from categories.models import Category

User = get_user_model()


class NutritionAPITestCase(APITestCase):
    """Integration tests for Nutrition API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category
        self.category = Category.objects.create(name='Main Course')
        
        # Create ingredients
        self.ingredient1 = Ingredient.objects.create(
            name='Tomato',
            description='Fresh tomato',
            unit='g'
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Onion',
            description='Yellow onion',
            unit='g'
        )
        
        # Create ingredient nutrition
        self.ingredient_nutrition1 = IngredientNutrition.objects.create(
            ingredient=self.ingredient1,
            calories_per_100g=18.0,
            protein_per_100g=0.9,
            carbohydrates_per_100g=3.9,
            fat_per_100g=0.2,
            fiber_per_100g=1.2,
            sugar_per_100g=2.6,
            sodium_per_100g=5.0
        )
        
        self.ingredient_nutrition2 = IngredientNutrition.objects.create(
            ingredient=self.ingredient2,
            calories_per_100g=40.0,
            protein_per_100g=1.1,
            carbohydrates_per_100g=9.3,
            fat_per_100g=0.1,
            fiber_per_100g=1.7,
            sugar_per_100g=4.2,
            sodium_per_100g=4.0
        )
        
        # Create recipe
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test description',
            instructions='Test instructions',
            prep_time=10,
            cook_time=20,
            servings=4,
            difficulty='easy',
            author=self.user,
            category=self.category,
            is_public=True
        )
        
        # Add ingredients to recipe
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient1,
            quantity='200g',
            order=1
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe,
            ingredient=self.ingredient2,
            quantity='100g',
            order=2
        )
        
        # Create recipe nutrition
        self.recipe_nutrition = Nutrition.objects.create(
            recipe=self.recipe,
            calories=76.0,
            protein=2.9,
            carbohydrates=17.1,
            fat=0.5,
            fiber=4.1,
            sugar=9.4,
            sodium=14.0
        )
    
    def test_calculate_nutrition_by_recipe_id(self):
        """Test POST /api/nutrition/calculate/ - Calculate nutrition by recipe ID"""
        data = {'recipe_id': self.recipe.id}
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['calories']), 76.0)
        self.assertEqual(float(response.data['protein']), 2.9)
        self.assertIn('carbohydrates', response.data)
        self.assertIn('fat', response.data)
    
    def test_calculate_nutrition_by_recipe_id_nonexistent(self):
        """Test POST /api/nutrition/calculate/ - Nonexistent recipe ID"""
        data = {'recipe_id': 99999}
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_calculate_nutrition_by_recipe_id_no_nutrition_data(self):
        """Test POST /api/nutrition/calculate/ - Recipe without nutrition data"""
        # Create recipe without nutrition
        recipe2 = Recipe.objects.create(
            title='Recipe Without Nutrition',
            description='Description',
            instructions='Instructions',
            prep_time=5,
            cook_time=10,
            servings=2,
            difficulty='easy',
            author=self.user,
            category=self.category
        )
        RecipeIngredient.objects.create(
            recipe=recipe2,
            ingredient=self.ingredient1,
            quantity='100g',
            order=1
        )
        
        data = {'recipe_id': recipe2.id}
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        # Should calculate from ingredients
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('calories', response.data)
        self.assertGreater(float(response.data['calories']), 0)
    
    def test_calculate_nutrition_by_ingredients(self):
        """Test POST /api/nutrition/calculate/ - Calculate nutrition by ingredients list"""
        data = {
            'ingredients': [
                {'ingredient_id': self.ingredient1.id, 'quantity': '200g'},
                {'ingredient_id': self.ingredient2.id, 'quantity': '100g'}
            ]
        }
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('calories', response.data)
        self.assertIn('protein', response.data)
        self.assertIn('carbohydrates', response.data)
        # Should calculate totals from ingredients
        # 200g tomato: 18 * 2 = 36 calories
        # 100g onion: 40 * 1 = 40 calories
        # Total: ~76 calories
        self.assertGreater(float(response.data['calories']), 0)
    
    def test_calculate_nutrition_by_ingredients_missing_quantity(self):
        """Test POST /api/nutrition/calculate/ - Missing quantity defaults to 100g"""
        data = {
            'ingredients': [
                {'ingredient_id': self.ingredient1.id}
            ]
        }
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use default 100g
        self.assertIn('calories', response.data)
    
    def test_calculate_nutrition_by_ingredients_nonexistent(self):
        """Test POST /api/nutrition/calculate/ - Nonexistent ingredient ID"""
        data = {
            'ingredients': [
                {'ingredient_id': 99999, 'quantity': '100g'}
            ]
        }
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should skip nonexistent ingredients
        self.assertIn('calories', response.data)
    
    def test_calculate_nutrition_missing_params(self):
        """Test POST /api/nutrition/calculate/ - Missing recipe_id and ingredients"""
        response = self.client.post('/api/nutrition/calculate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_ingredient_nutrition(self):
        """Test GET /api/nutrition/ingredients/:id/ - Get ingredient nutrition"""
        response = self.client.get(f'/api/nutrition/ingredients/{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['calories_per_100g']), 18.0)
        self.assertEqual(float(response.data['protein_per_100g']), 0.9)
        self.assertIn('carbohydrates_per_100g', response.data)
        self.assertIn('fat_per_100g', response.data)
    
    def test_get_ingredient_nutrition_nonexistent_ingredient(self):
        """Test GET /api/nutrition/ingredients/:id/ - Nonexistent ingredient"""
        response = self.client.get('/api/nutrition/ingredients/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_get_ingredient_nutrition_no_data(self):
        """Test GET /api/nutrition/ingredients/:id/ - Ingredient without nutrition data"""
        # Create ingredient without nutrition
        ingredient3 = Ingredient.objects.create(
            name='Salt',
            description='Table salt',
            unit='g'
        )
        response = self.client.get(f'/api/nutrition/ingredients/{ingredient3.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_calculate_nutrition_recipe_with_ingredients(self):
        """Test POST /api/nutrition/calculate/ - Calculate from recipe ingredients"""
        # Delete existing nutrition to test calculation
        self.recipe_nutrition.delete()
        
        data = {'recipe_id': self.recipe.id}
        response = self.client.post('/api/nutrition/calculate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should calculate from recipe ingredients
        self.assertIn('calories', response.data)
        self.assertGreater(float(response.data['calories']), 0)
        # 200g tomato + 100g onion
        # Approximate: (18 * 2) + (40 * 1) = 76 calories
        self.assertAlmostEqual(float(response.data['calories']), 76.0, delta=10.0)
