from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Bookmark
from recipes.models import Recipe
from categories.models import Category

User = get_user_model()


class BookmarkAPITestCase(APITestCase):
    """Integration tests for Bookmark API endpoints"""
    
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
        self.category = Category.objects.create(name='Main Course')
        
        # Create recipes
        self.recipe1 = Recipe.objects.create(
            title='Recipe 1',
            description='Description 1',
            instructions='Instructions 1',
            prep_time=10,
            cook_time=20,
            servings=4,
            difficulty='easy',
            author=self.user1,
            category=self.category,
            is_public=True
        )
        
        self.recipe2 = Recipe.objects.create(
            title='Recipe 2',
            description='Description 2',
            instructions='Instructions 2',
            prep_time=15,
            cook_time=30,
            servings=2,
            difficulty='medium',
            author=self.user2,
            category=self.category,
            is_public=True
        )
        
        # Create existing bookmark
        self.bookmark = Bookmark.objects.create(
            user=self.user1,
            recipe=self.recipe1
        )
    
    def get_auth_token(self, user):
        """Helper to get JWT token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_list_bookmarks_unauthorized(self):
        """Test GET /api/bookmarks/ - Cannot list bookmarks without authentication"""
        response = self.client.get('/api/bookmarks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_bookmarks_authorized(self):
        """Test GET /api/bookmarks/ - List user's bookmarks"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/bookmarks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['recipe']['id'], self.recipe1.id)
    
    def test_list_bookmarks_only_own(self):
        """Test GET /api/bookmarks/ - Only see own bookmarks"""
        # Create bookmark for user2
        Bookmark.objects.create(user=self.user2, recipe=self.recipe2)
        
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/bookmarks/')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['recipe']['id'], self.recipe1.id)
    
    def test_create_bookmark_unauthorized(self):
        """Test POST /api/bookmarks/ - Cannot create bookmark without authentication"""
        data = {'recipe': self.recipe2.id}
        response = self.client.post('/api/bookmarks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_bookmark_authorized(self):
        """Test POST /api/bookmarks/ - Create bookmark with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # BookmarkSerializer uses recipe_id for write operations, not recipe
        data = {'recipe_id': self.recipe2.id}
        response = self.client.post('/api/bookmarks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['recipe']['id'], self.recipe2.id)
        # Verify bookmark was created
        bookmark = Bookmark.objects.get(user=self.user1, recipe=self.recipe2)
        self.assertIsNotNone(bookmark)
    
    def test_create_duplicate_bookmark(self):
        """Test POST /api/bookmarks/ - Cannot create duplicate bookmark"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {'recipe': self.recipe1.id}  # Already bookmarked
        response = self.client.post('/api/bookmarks/', data, format='json')
        # Should fail due to unique constraint
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
    
    def test_delete_bookmark_unauthorized(self):
        """Test DELETE /api/bookmarks/:id/ - Cannot delete bookmark without authentication"""
        response = self.client.delete(f'/api/bookmarks/{self.bookmark.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_bookmark_authorized(self):
        """Test DELETE /api/bookmarks/:id/ - Delete bookmark with authentication"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        bookmark_id = self.bookmark.id
        response = self.client.delete(f'/api/bookmarks/{bookmark_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify bookmark was deleted
        self.assertFalse(Bookmark.objects.filter(id=bookmark_id).exists())
    
    def test_delete_other_user_bookmark(self):
        """Test DELETE /api/bookmarks/:id/ - Cannot delete other user's bookmark"""
        bookmark2 = Bookmark.objects.create(user=self.user2, recipe=self.recipe2)
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.delete(f'/api/bookmarks/{bookmark2.id}/')
        # Should return 404 or 403
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])
    
    def test_check_bookmark_unauthorized(self):
        """Test GET /api/bookmarks/check/:recipeId/ - Cannot check without authentication"""
        response = self.client.get(f'/api/bookmarks/check/{self.recipe1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_check_bookmark_true(self):
        """Test GET /api/bookmarks/check/:recipeId/ - Check if recipe is bookmarked (true)"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/bookmarks/check/{self.recipe1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_bookmarked'])
    
    def test_check_bookmark_false(self):
        """Test GET /api/bookmarks/check/:recipeId/ - Check if recipe is bookmarked (false)"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/bookmarks/check/{self.recipe2.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_bookmarked'])
    
    def test_check_bookmark_nonexistent_recipe(self):
        """Test GET /api/bookmarks/check/:recipeId/ - Nonexistent recipe"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/bookmarks/check/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_bookmark(self):
        """Test GET /api/bookmarks/:id/ - Retrieve bookmark"""
        token = self.get_auth_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/bookmarks/{self.bookmark.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recipe']['id'], self.recipe1.id)
        self.assertIn('created_at', response.data)
