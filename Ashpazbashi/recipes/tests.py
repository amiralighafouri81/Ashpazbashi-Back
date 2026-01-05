from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Recipe, RecipeIngredient, RecipeRating, RecipeGeneration
from ingredients.models import Ingredient
from categories.models import Category, Tag, DietaryType

User = get_user_model()


class RecipeAPITestCase(APITestCase):
    """Integration tests for Recipe API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Main Course',
            description='Main course recipes'
        )
        
        # Create tags
        self.tag1 = Tag.objects.create(name='Italian')
        self.tag2 = Tag.objects.create(name='Quick')
        
        # Create dietary types
        self.dietary_type = DietaryType.objects.create(name='Vegetarian')
        
        # Create ingredients
        self.ingredient1 = Ingredient.objects.create(name='Tomato', unit='g')
        self.ingredient2 = Ingredient.objects.create(name='Onion', unit='g')
        self.ingredient3 = Ingredient.objects.create(name='Garlic', unit='g')
        
        # Create recipes
        self.recipe1 = Recipe.objects.create(
            title='Test Recipe 1',
            description='A test recipe',
            instructions='Step 1, Step 2',
            prep_time=10,
            cook_time=20,
            servings=4,
            difficulty='easy',
            author=self.user1,
            category=self.category,
            is_public=True
        )
        self.recipe1.tags.add(self.tag1)
        self.recipe1.dietary_types.add(self.dietary_type)
        
        # Add ingredients to recipe
        RecipeIngredient.objects.create(
            recipe=self.recipe1,
            ingredient=self.ingredient1,
            quantity='200g',
            order=1
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe1,
            ingredient=self.ingredient2,
            quantity='100g',
            order=2
        )
        
        self.recipe2 = Recipe.objects.create(
            title='Test Recipe 2',
            description='Another test recipe',
            instructions='Instructions here',
            prep_time=15,
            cook_time=30,
            servings=2,
            difficulty='medium',
            author=self.user2,
            category=self.category,
            is_public=True
        )
        
        # Private recipe
        self.private_recipe = Recipe.objects.create(
            title='Private Recipe',
            description='Private recipe',
            instructions='Private instructions',
            prep_time=5,
            cook_time=10,
            servings=1,
            difficulty='easy',
            author=self.user1,
            is_public=False
        )
    
    def get_auth_token(self, user):
        """Helper to get JWT token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_list_recipes_unauthorized(self):
        """Test GET /api/recipes/ - List recipes without authentication"""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        # Should only return public recipes
        recipe_titles = [r['title'] for r in response.data['results']]
        self.assertIn('Test Recipe 1', recipe_titles)
        self.assertIn('Test Recipe 2', recipe_titles)
        self.assertNotIn('Private Recipe', recipe_titles)
    
    def test_list_recipes_authorized(self):
        """Test GET /api/recipes/ - List recipes with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should include user's own private recipes
        recipe_titles = [r['title'] for r in response.data['results']]
        self.assertIn('Private Recipe', recipe_titles)
    
    def test_list_recipes_with_filters(self):
        """Test GET /api/recipes/ - Filter by category and difficulty"""
        response = self.client.get('/api/recipes/', {
            'category': self.category.id,
            'difficulty': 'easy'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for recipe in response.data['results']:
            self.assertEqual(recipe['difficulty'], 'easy')
    
    def test_list_recipes_search(self):
        """Test GET /api/recipes/ - Search recipes"""
        response = self.client.get('/api/recipes/', {'search': 'Test Recipe 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Recipe 1')
    
    def test_retrieve_recipe_unauthorized(self):
        """Test GET /api/recipes/:id/ - Retrieve recipe without authentication"""
        response = self.client.get(f'/api/recipes/{self.recipe1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Recipe 1')
        self.assertIn('recipe_ingredients', response.data)
        self.assertIn('ratings', response.data)
        # Check that views_count is incremented
        # Note: The view only increments views_count if user is authenticated
        # So for unauthenticated users, it won't increment
        self.recipe1.refresh_from_db()
        # views_count should remain 0 for unauthenticated users
        self.assertEqual(self.recipe1.views_count, 0)
    
    def test_retrieve_recipe_authorized(self):
        """Test GET /api/recipes/:id/ - Retrieve recipe with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/recipes/{self.recipe1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that history is created
        from history.models import RecipeHistory
        history = RecipeHistory.objects.filter(
            user=self.user1,
            recipe=self.recipe1
        ).first()
        self.assertIsNotNone(history)
    
    def test_retrieve_private_recipe_unauthorized(self):
        """Test GET /api/recipes/:id/ - Cannot retrieve private recipe without auth"""
        response = self.client.get(f'/api/recipes/{self.private_recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_recipe_unauthorized(self):
        """Test POST /api/recipes/ - Cannot create recipe without authentication"""
        data = {
            'title': 'New Recipe',
            'description': 'New description',
            'instructions': 'New instructions',
            'prep_time': 10,
            'cook_time': 20,
            'servings': 4,
            'difficulty': 'easy',
            'category_id': self.category.id,
            'tag_ids': [self.tag1.id],
        }
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_recipe_authorized(self):
        """Test POST /api/recipes/ - Create recipe with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'title': 'New Recipe',
            'description': 'New description',
            'instructions': 'New instructions',
            'prep_time': 10,
            'cook_time': 20,
            'servings': 4,
            'difficulty': 'easy',
            'category_id': self.category.id,
            'tag_ids': [self.tag1.id, self.tag2.id],
            'dietary_type_ids': [self.dietary_type.id],
        }
        response = self.client.post('/api/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Recipe')
        self.assertEqual(response.data['author']['username'], 'testuser1')
        # Verify recipe was created
        recipe = Recipe.objects.get(title='New Recipe')
        self.assertEqual(recipe.author, self.user1)
        self.assertEqual(recipe.tags.count(), 2)
    
    def test_rate_recipe_unauthorized(self):
        """Test POST /api/recipes/:id/rate/ - Cannot rate without authentication"""
        data = {'rating': 5, 'comment': 'Great recipe!'}
        response = self.client.post(
            f'/api/recipes/{self.recipe1.id}/rate/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_rate_recipe_authorized(self):
        """Test POST /api/recipes/:id/rate/ - Rate recipe with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'rating': 5, 'comment': 'Great recipe!'}
        response = self.client.post(
            f'/api/recipes/{self.recipe1.id}/rate/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)
        # Verify rating was created
        rating = RecipeRating.objects.get(recipe=self.recipe1, user=self.user1)
        self.assertEqual(rating.rating, 5)
        # Verify average rating was updated
        self.recipe1.refresh_from_db()
        self.assertEqual(self.recipe1.average_rating, 5.0)
        self.assertEqual(self.recipe1.ratings_count, 1)
    
    def test_rate_recipe_update_existing(self):
        """Test POST /api/recipes/:id/rate/ - Update existing rating"""
        # Create initial rating
        RecipeRating.objects.create(
            recipe=self.recipe1,
            user=self.user1,
            rating=3
        )
        self.recipe1.refresh_from_db()
        
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'rating': 5, 'comment': 'Updated rating'}
        response = self.client.post(
            f'/api/recipes/{self.recipe1.id}/rate/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify only one rating exists
        self.assertEqual(RecipeRating.objects.filter(
            recipe=self.recipe1,
            user=self.user1
        ).count(), 1)
        rating = RecipeRating.objects.get(recipe=self.recipe1, user=self.user1)
        self.assertEqual(rating.rating, 5)
    
    def test_rate_recipe_invalid_rating(self):
        """Test POST /api/recipes/:id/rate/ - Invalid rating value"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'rating': 6}  # Invalid rating
        response = self.client.post(
            f'/api/recipes/{self.recipe1.id}/rate/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_by_ingredients(self):
        """Test POST /api/recipes/by-ingredients/ - Find recipes by ingredients"""
        # Note: get_permissions() overrides the action's AllowAny permission
        # So we need authentication even though the action decorator says AllowAny
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'ingredient_ids': [self.ingredient1.id, self.ingredient2.id]}
        response = self.client.post(
            '/api/recipes/by-ingredients/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        # Recipe1 should be in results
        recipe_ids = [r['id'] for r in response.data]
        self.assertIn(self.recipe1.id, recipe_ids)
    
    def test_by_ingredients_missing_ingredient_ids(self):
        """Test POST /api/recipes/by-ingredients/ - Missing ingredient_ids"""
        # Note: get_permissions() overrides the action's AllowAny permission
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/recipes/by-ingredients/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_similar_recipes(self):
        """Test GET /api/recipes/:id/similar/ - Get similar recipes"""
        # The action has AllowAny permission, but get_object() might require auth
        # Let's test with authentication to be safe
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/recipes/{self.recipe1.id}/similar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return similar recipes (same category)
        recipe_ids = [r['id'] for r in response.data]
        self.assertIn(self.recipe2.id, recipe_ids)
        # Should not include the recipe itself
        self.assertNotIn(self.recipe1.id, recipe_ids)
    
    def test_generate_recipe_unauthorized(self):
        """Test POST /api/recipes/generate/ - Cannot generate without authentication"""
        data = {'prompt': 'Create a pasta recipe'}
        response = self.client.post('/api/recipes/generate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_generate_recipe_authorized(self):
        """Test POST /api/recipes/generate/ - Generate recipe with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'prompt': 'Create a pasta recipe'}
        response = self.client.post('/api/recipes/generate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'pending')
        # Verify generation was created
        generation = RecipeGeneration.objects.filter(
            user=self.user1,
            prompt='Create a pasta recipe'
        ).first()
        self.assertIsNotNone(generation)
    
    def test_generate_recipe_missing_prompt(self):
        """Test POST /api/recipes/generate/ - Missing prompt"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/recipes/generate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_recipe_unauthorized(self):
        """Test PUT /api/recipes/:id/ - Cannot update without authentication"""
        data = {'title': 'Updated Title'}
        response = self.client.put(
            f'/api/recipes/{self.recipe1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_recipe_authorized(self):
        """Test PUT /api/recipes/:id/ - Update recipe with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'title': 'Updated Recipe Title',
            'description': 'Updated description',
            'instructions': 'Updated instructions',
            'prep_time': 15,
            'cook_time': 25,
            'servings': 6,
            'difficulty': 'medium',
        }
        response = self.client.put(
            f'/api/recipes/{self.recipe1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Recipe Title')
        self.recipe1.refresh_from_db()
        self.assertEqual(self.recipe1.title, 'Updated Recipe Title')
    
    def test_delete_recipe_unauthorized(self):
        """Test DELETE /api/recipes/:id/ - Cannot delete without authentication"""
        response = self.client.delete(f'/api/recipes/{self.recipe1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_recipe_authorized(self):
        """Test DELETE /api/recipes/:id/ - Delete recipe with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        recipe_id = self.recipe1.id
        response = self.client.delete(f'/api/recipes/{recipe_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify recipe was deleted
        self.assertFalse(Recipe.objects.filter(id=recipe_id).exists())


class GenerationViewSetTestCase(APITestCase):
    """Integration tests for Generation ViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.generation = RecipeGeneration.objects.create(
            user=self.user,
            prompt='Test prompt',
            status='pending'
        )
    
    def get_auth_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_list_generations_unauthorized(self):
        """Test GET /api/generation/ - Cannot list without authentication"""
        response = self.client.get('/api/generation/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_generations_authorized(self):
        """Test GET /api/generation/ - List user's generations"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/generation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.generation.id)
    
    def test_list_generations_only_own(self):
        """Test GET /api/generation/ - Only see own generations"""
        # Create generation for other user
        RecipeGeneration.objects.create(
            user=self.other_user,
            prompt='Other prompt',
            status='pending'
        )
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/generation/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.generation.id)
    
    def test_get_generation_status(self):
        """Test GET /api/generation/:id/status/ - Get generation status"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/generation/{self.generation.id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['id'], self.generation.id)
    
    def test_get_generation_result_pending(self):
        """Test GET /api/generation/:id/result/ - Get result when pending"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/generation/{self.generation.id}/result/')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'pending')
    
    def test_get_generation_result_completed(self):
        """Test GET /api/generation/:id/result/ - Get result when completed"""
        # Create a recipe and link it to generation
        category = Category.objects.create(name='Test Category')
        recipe = Recipe.objects.create(
            title='Generated Recipe',
            description='Generated',
            instructions='Instructions',
            prep_time=10,
            cook_time=20,
            servings=4,
            difficulty='easy',
            author=self.user,
            category=category
        )
        self.generation.recipe = recipe
        self.generation.status = 'completed'
        self.generation.save()
        
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/generation/{self.generation.id}/result/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Generated Recipe')
    
    def test_get_generation_result_failed(self):
        """Test GET /api/generation/:id/result/ - Get result when failed"""
        self.generation.status = 'failed'
        self.generation.error_message = 'Generation failed'
        self.generation.save()
        
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/generation/{self.generation.id}/result/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
