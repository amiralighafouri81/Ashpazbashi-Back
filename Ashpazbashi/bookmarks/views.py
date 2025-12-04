from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Bookmark
from .serializers import BookmarkSerializer
from recipes.models import Recipe


class BookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for Bookmark operations"""
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('recipe', 'user')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='check/(?P<recipe_id>[^/.]+)', permission_classes=[permissions.IsAuthenticated])
    def check(self, request, recipe_id=None):
        """GET /api/bookmarks/check/:recipeId - Check if recipe is bookmarked"""
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            is_bookmarked = Bookmark.objects.filter(user=request.user, recipe=recipe).exists()
            return Response({'is_bookmarked': is_bookmarked})
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )
