from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RecipeShare
from .serializers import RecipeShareSerializer
from recipes.models import Recipe


class ShareViewSet(viewsets.ModelViewSet):
    """ViewSet for Recipe Sharing operations"""
    serializer_class = RecipeShareSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'share_id'
    
    def get_queryset(self):
        return RecipeShare.objects.all().select_related('recipe', 'created_by')
    
    @action(detail=False, methods=['post'], url_path='recipes/(?P<recipe_id>[^/.]+)/share', permission_classes=[permissions.IsAuthenticated])
    def create_share(self, request, recipe_id=None):
        """POST /api/recipes/:id/share - Create share link for recipe"""
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            share, created = RecipeShare.objects.get_or_create(
                recipe=recipe,
                created_by=request.user
            )
            serializer = self.get_serializer(share)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/share/:shareId - Get shared recipe"""
        instance = self.get_object()
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
