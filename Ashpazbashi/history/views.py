from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RecipeHistory
from .serializers import RecipeHistorySerializer
from recipes.models import Recipe


class HistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Recipe History operations"""
    serializer_class = RecipeHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RecipeHistory.objects.filter(user=self.request.user).select_related('recipe').order_by('-viewed_at')
    
    @action(detail=False, methods=['post'], url_path='(?P<recipe_id>[^/.]+)', permission_classes=[permissions.IsAuthenticated])
    def add(self, request, recipe_id=None):
        """POST /api/history/:recipeId - Add recipe to history"""
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            history, created = RecipeHistory.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                # Update viewed_at timestamp
                history.save()
            serializer = self.get_serializer(history)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'], url_path='clear', permission_classes=[permissions.IsAuthenticated])
    def clear(self, request):
        """DELETE /api/history - Clear all history"""
        RecipeHistory.objects.filter(user=request.user).delete()
        return Response({'message': 'History cleared'}, status=status.HTTP_200_OK)
