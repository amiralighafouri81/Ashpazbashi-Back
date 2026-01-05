"""
ChromaDB client utility for hybrid search functionality.

This module provides functions to query ChromaDB for semantic search
while keeping PostgreSQL for structured queries and user interactions.
"""

import os
import json
from typing import List, Dict, Optional
from django.conf import settings


class ChromaDBClient:
    """Client for interacting with ChromaDB API"""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or getattr(settings, 'CHROMADB_URL', 'http://localhost:8324')
        self.token = token or getattr(settings, 'CHROMADB_TOKEN', os.getenv('CHROMA_ACCESS_TOKEN'))
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        } if self.token else {'Content-Type': 'application/json'}

    def search(
        self,
        query: str = '',
        include_ingredients: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search recipes in ChromaDB.

        Args:
            query: Text query for semantic search
            include_ingredients: List of ingredient names to filter by
            limit: Maximum number of results

        Returns:
            List of recipe dictionaries
        """
        try:
            import requests
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('requests module not installed. ChromaDB search unavailable.')
            return []

        url = f'{self.base_url}/search'
        payload = {
            'query': query,
            'limit': limit
        }

        if include_ingredients:
            payload['include_ingredients'] = include_ingredients

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Log error but don't fail - fallback to PostgreSQL
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'ChromaDB search failed: {e}')
            return []

    def get_by_foodname(self, foodname: str) -> Optional[Dict]:
        """Get a recipe by exact foodname match"""
        results = self.search(query=foodname, limit=1)
        if results and results[0].get('foodname') == foodname:
            return results[0]
        return None


def get_chromadb_client() -> ChromaDBClient:
    """Get a configured ChromaDB client instance"""
    return ChromaDBClient()


def map_chromadb_to_postgres_ids(chromadb_results: List[Dict]) -> List[int]:
    """
    Map ChromaDB search results to PostgreSQL recipe IDs.

    This function searches PostgreSQL for recipes matching ChromaDB results
    by foodname (title) and returns their IDs.

    Args:
        chromadb_results: List of recipe dicts from ChromaDB

    Returns:
        List of PostgreSQL recipe IDs
    """
    from recipes.models import Recipe

    recipe_ids = []
    for result in chromadb_results:
        foodname = result.get('foodname', '').strip()
        if foodname:
            try:
                recipe = Recipe.objects.filter(title=foodname, is_public=True).first()
                if recipe:
                    recipe_ids.append(recipe.id)
            except Exception:
                # Skip if recipe not found or error
                continue

    return recipe_ids

