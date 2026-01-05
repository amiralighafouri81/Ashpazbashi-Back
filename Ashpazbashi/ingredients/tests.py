from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Ingredient, IngredientSubstitute

User = get_user_model()


class IngredientAPITestCase(APITestCase):
    """Integration tests for Ingredient API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create ingredients
        self.ingredient1 = Ingredient.objects.create(
            name='Tomato',
            description='Fresh red tomato',
            unit='g'
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Onion',
            description='Yellow onion',
            unit='g'
        )
        self.ingredient3 = Ingredient.objects.create(
            name='Garlic',
            description='Fresh garlic cloves',
            unit='g'
        )
        self.ingredient4 = Ingredient.objects.create(
            name='Tomato Paste',
            description='Concentrated tomato paste',
            unit='g'
        )
        
        # Create substitutes
        self.substitute1 = IngredientSubstitute.objects.create(
            original_ingredient=self.ingredient1,
            substitute_ingredient=self.ingredient4,
            substitution_ratio='1:1',
            notes='Can use tomato paste as substitute'
        )
    
    def test_list_ingredients(self):
        """Test GET /api/ingredients/ - List all ingredients"""
        response = self.client.get('/api/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        # Should be ordered by name
        names = [ing['name'] for ing in response.data['results']]
        self.assertEqual(names, sorted(names))
    
    def test_list_ingredients_search(self):
        """Test GET /api/ingredients/ - Search ingredients"""
        response = self.client.get('/api/ingredients/', {'search': 'Tomato'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return ingredients with 'Tomato' in name
        names = [ing['name'] for ing in response.data['results']]
        self.assertIn('Tomato', names)
        self.assertIn('Tomato Paste', names)
    
    def test_retrieve_ingredient(self):
        """Test GET /api/ingredients/:id/ - Retrieve ingredient"""
        response = self.client.get(f'/api/ingredients/{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Tomato')
        self.assertEqual(response.data['description'], 'Fresh red tomato')
        self.assertIn('created_at', response.data)
    
    def test_retrieve_nonexistent_ingredient(self):
        """Test GET /api/ingredients/:id/ - Nonexistent ingredient"""
        response = self.client.get('/api/ingredients/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_search_ingredients_action(self):
        """Test GET /api/ingredients/search/ - Search ingredients action"""
        response = self.client.get('/api/ingredients/search/', {'q': 'Tomato'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        names = [ing['name'] for ing in response.data]
        self.assertIn('Tomato', names)
    
    def test_search_ingredients_missing_query(self):
        """Test GET /api/ingredients/search/ - Missing query parameter"""
        response = self.client.get('/api/ingredients/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_ingredient_substitutes(self):
        """Test GET /api/ingredients/:id/substitutes/ - Get substitutes for ingredient"""
        response = self.client.get(f'/api/ingredients/{self.ingredient1.id}/substitutes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['substitute_ingredient']['id'], self.ingredient4.id)
        self.assertEqual(response.data[0]['substitution_ratio'], '1:1')
    
    def test_get_ingredient_substitutes_none(self):
        """Test GET /api/ingredients/:id/substitutes/ - No substitutes available"""
        response = self.client.get(f'/api/ingredients/{self.ingredient2.id}/substitutes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_substitute_ingredients_action(self):
        """Test POST /api/ingredients/substitute/ - Suggest substitutes for ingredients"""
        data = {'ingredient_ids': [self.ingredient1.id, self.ingredient2.id]}
        response = self.client.post('/api/ingredients/substitute/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Check that ingredient1 has substitutes
        ingredient1_data = next(
            (item for item in response.data if item['ingredient']['id'] == self.ingredient1.id),
            None
        )
        self.assertIsNotNone(ingredient1_data)
        self.assertGreater(len(ingredient1_data['substitutes']), 0)
    
    def test_substitute_ingredients_missing_ids(self):
        """Test POST /api/ingredients/substitute/ - Missing ingredient_ids"""
        response = self.client.post('/api/ingredients/substitute/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_substitute_ingredients_nonexistent(self):
        """Test POST /api/ingredients/substitute/ - Nonexistent ingredient IDs"""
        data = {'ingredient_ids': [99999, 99998]}
        response = self.client.post('/api/ingredients/substitute/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty list for nonexistent ingredients
        self.assertEqual(len(response.data), 0)
    
    def test_list_ingredients_filtered(self):
        """Test GET /api/ingredients/ - Filter ingredients"""
        response = self.client.get('/api/ingredients/', {'name': 'Tomato'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Results should contain Tomato
        names = [ing['name'] for ing in response.data['results']]
        self.assertIn('Tomato', names)
    
    def test_list_ingredients_ordered(self):
        """Test GET /api/ingredients/ - Order ingredients"""
        response = self.client.get('/api/ingredients/', {'ordering': '-name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [ing['name'] for ing in response.data['results']]
        self.assertEqual(names, sorted(names, reverse=True))
