from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Ingredient, IngredientSubstitute
from .serializers import IngredientSerializer, IngredientSubstituteSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Ingredient read operations"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def search(self, request):
        """GET /api/ingredients/search - Search ingredients"""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ingredients = Ingredient.objects.filter(name__icontains=query)
        serializer = self.get_serializer(ingredients, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def substitutes(self, request, pk=None):
        """GET /api/ingredients/:id/substitutes - Get substitutes for an ingredient"""
        ingredient = self.get_object()
        substitutes = IngredientSubstitute.objects.filter(original_ingredient=ingredient)
        serializer = IngredientSubstituteSerializer(substitutes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def substitute(self, request):
        """POST /api/ingredients/substitute - Suggest substitutes for ingredients"""
        ingredient_ids = request.data.get('ingredient_ids', [])
        if not ingredient_ids:
            return Response(
                {'error': 'ingredient_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        substitutes = []
        for ingredient_id in ingredient_ids:
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
                ingredient_subs = IngredientSubstitute.objects.filter(original_ingredient=ingredient)
                subs_data = IngredientSubstituteSerializer(ingredient_subs, many=True).data
                substitutes.append({
                    'ingredient': IngredientSerializer(ingredient).data,
                    'substitutes': subs_data
                })
            except Ingredient.DoesNotExist:
                continue
        
        return Response(substitutes)
