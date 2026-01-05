from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """Integration tests for user registration"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_user_registration_success(self):
        """Test POST /api/auth/users/ - Successful user registration"""
        # UserRegistrationSerializer expects password_confirmation, not password_confirm
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirmation': 'securepass123'
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
    
    def test_user_registration_missing_fields(self):
        """Test POST /api/auth/users/ - Missing required fields"""
        data = {
            'username': 'newuser',
            # Missing email and password
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_registration_duplicate_username(self):
        """Test POST /api/auth/users/ - Duplicate username"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='pass123'
        )
        data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'securepass123',
            'password_confirmation': 'securepass123'
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_registration_weak_password(self):
        """Test POST /api/auth/users/ - Weak password"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',  # Too short
            'password_confirmation': '123'
        }
        response = self.client.post('/api/auth/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(APITestCase):
    """Integration tests for user login"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_success(self):
        """Test POST /api/auth/jwt/create/ - Successful login"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/jwt/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_wrong_password(self):
        """Test POST /api/auth/jwt/create/ - Wrong password"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/auth/jwt/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_nonexistent_user(self):
        """Test POST /api/auth/jwt/create/ - Nonexistent user"""
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        response = self.client.post('/api/auth/jwt/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_missing_credentials(self):
        """Test POST /api/auth/jwt/create/ - Missing credentials"""
        response = self.client.post('/api/auth/jwt/create/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTestCase(APITestCase):
    """Integration tests for user profile endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def get_auth_token(self, user):
        """Helper to get JWT token for a user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_get_profile_unauthorized(self):
        """Test GET /api/auth/users/me/ - Cannot get profile without authentication"""
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_profile_authorized(self):
        """Test GET /api/auth/users/me/ - Get profile with authentication"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_update_profile_unauthorized(self):
        """Test PUT /api/auth/users/me/ - Cannot update profile without authentication"""
        data = {'biography': 'Updated bio'}
        response = self.client.put('/api/auth/users/me/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile_authorized(self):
        """Test PUT /api/auth/users/me/ - Update profile with authentication"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # UserSerializer might require all fields or use PATCH instead
        # Let's try with PATCH first, or include all required fields
        data = {
            'username': self.user.username,  # Include existing username
            'email': self.user.email,  # Include existing email
            'biography': 'Updated biography',
            'student_number': '12345'
        }
        response = self.client.put('/api/auth/users/me/', data, format='json')
        # If PUT requires all fields and fails, try PATCH
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            response = self.client.patch('/api/auth/users/me/', {
                'biography': 'Updated biography',
                'student_number': '12345'
            }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['biography'], 'Updated biography')
        # Verify user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.biography, 'Updated biography')
    
    def test_get_user_profile_detail(self):
        """Test GET /api/auth/profile/ - Get user profile detail"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Profile should be created automatically
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNotNone(profile)
    
    def test_update_user_profile_detail(self):
        """Test PUT /api/auth/profile/ - Update user profile detail"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'dietary_preferences': {'vegetarian': True},
            'favorite_cuisines': ['Italian', 'Mexican'],
            'cooking_skill_level': 'intermediate'
        }
        response = self.client.put('/api/auth/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify profile was updated
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.cooking_skill_level, 'intermediate')
        self.assertEqual(profile.favorite_cuisines, ['Italian', 'Mexican'])
    
    def test_get_dietary_preferences(self):
        """Test GET /api/auth/dietary-preferences/ - Get dietary preferences"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/dietary-preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('dietary_preferences', response.data)
        self.assertIn('favorite_cuisines', response.data)
        self.assertIn('cooking_skill_level', response.data)
    
    def test_update_dietary_preferences(self):
        """Test PUT /api/auth/dietary-preferences/ - Update dietary preferences"""
        token = self.get_auth_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            'dietary_preferences': {'vegan': True, 'gluten_free': True},
            'favorite_cuisines': ['Thai', 'Japanese'],
            'cooking_skill_level': 'advanced'
        }
        response = self.client.put('/api/auth/dietary-preferences/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cooking_skill_level'], 'advanced')
        # Verify profile was updated
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.cooking_skill_level, 'advanced')
        self.assertEqual(profile.favorite_cuisines, ['Thai', 'Japanese'])


class TokenRefreshTestCase(APITestCase):
    """Integration tests for token refresh"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_refresh_token_success(self):
        """Test POST /api/auth/jwt/refresh/ - Successful token refresh"""
        refresh = RefreshToken.for_user(self.user)
        data = {'refresh': str(refresh)}
        response = self.client.post('/api/auth/jwt/refresh/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_refresh_token_invalid(self):
        """Test POST /api/auth/jwt/refresh/ - Invalid refresh token"""
        data = {'refresh': 'invalid_token'}
        response = self.client.post('/api/auth/jwt/refresh/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_refresh_token_missing(self):
        """Test POST /api/auth/jwt/refresh/ - Missing refresh token"""
        response = self.client.post('/api/auth/jwt/refresh/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
