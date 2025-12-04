from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from .models import Recipe, RecipeIngredient, RecipeRating, RecipeGeneration
from .serializers import (
    RecipeListSerializer, RecipeDetailSerializer, RecipeRatingSerializer,
    RecipeGenerationSerializer
)
from ingredients.models import Ingredient
from categories.models import Category, Tag, DietaryType
from history.models import RecipeHistory


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet for Recipe CRUD operations"""
    queryset = Recipe.objects.filter(is_public=True).select_related('author', 'category').prefetch_related('tags', 'dietary_types')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty', 'tags', 'dietary_types', 'author']
    search_fields = ['title', 'description', 'tags__name']
    ordering_fields = ['created_at', 'average_rating', 'views_count', 'prep_time', 'cook_time']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeListSerializer
        return RecipeDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            # Include user's own recipes even if not public
            queryset = Recipe.objects.filter(
                Q(is_public=True) | Q(author=self.request.user)
            ).select_related('author', 'category').prefetch_related('tags', 'dietary_types')
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Track view history if user is authenticated
        if request.user.is_authenticated:
            RecipeHistory.objects.create(user=request.user, recipe=instance)
            instance.views_count += 1
            instance.save(update_fields=['views_count'])
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def generate(self, request):
        """POST /api/recipes/generate - Generate recipe using AI"""
        prompt = request.data.get('prompt', '')
        if not prompt:
            return Response(
                {'error': 'Prompt is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create generation record
        generation = RecipeGeneration.objects.create(
            user=request.user,
            prompt=prompt,
            status='pending'
        )
        
        # TODO: Integrate with AI service (OpenAI, etc.)
        # For now, return pending status
        return Response(
            RecipeGenerationSerializer(generation).data,
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def by_ingredients(self, request):
        """POST /api/recipes/by-ingredients - Find recipes by available ingredients"""
        ingredient_ids = request.data.get('ingredient_ids', [])
        if not ingredient_ids:
            return Response(
                {'error': 'ingredient_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find recipes that contain at least one of the provided ingredients
        recipes = Recipe.objects.filter(
            recipe_ingredients__ingredient_id__in=ingredient_ids,
            is_public=True
        ).distinct().annotate(
            matching_ingredients=Count('recipe_ingredients__ingredient_id', filter=Q(recipe_ingredients__ingredient_id__in=ingredient_ids))
        ).order_by('-matching_ingredients', '-average_rating')
        
        serializer = RecipeListSerializer(recipes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def similar(self, request, pk=None):
        """GET /api/recipes/:id/similar - Get similar recipes"""
        recipe = self.get_object()
        
        # Find similar recipes based on:
        # 1. Same category
        # 2. Shared ingredients
        # 3. Shared tags
        
        similar = Recipe.objects.filter(
            Q(category=recipe.category) |
            Q(recipe_ingredients__ingredient__in=recipe.recipe_ingredients.values_list('ingredient', flat=True)) |
            Q(tags__in=recipe.tags.all())
        ).exclude(id=recipe.id).filter(is_public=True).distinct()[:10]
        
        serializer = RecipeListSerializer(similar, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, pk=None):
        """POST /api/recipes/:id/rate - Rate a recipe"""
        recipe = self.get_object()
        rating_value = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not rating_value or not (1 <= int(rating_value) <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rating, created = RecipeRating.objects.update_or_create(
            recipe=recipe,
            user=request.user,
            defaults={'rating': int(rating_value), 'comment': comment}
        )
        
        # Update recipe average rating
        ratings = RecipeRating.objects.filter(recipe=recipe)
        recipe.average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        recipe.ratings_count = ratings.count()
        recipe.save()
        
        return Response(RecipeRatingSerializer(rating).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class GenerationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Recipe Generation status and results"""
    queryset = RecipeGeneration.objects.all()
    serializer_class = RecipeGenerationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RecipeGeneration.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def status(self, request, pk=None):
        """GET /api/generation/:generationId/status - Get generation status"""
        generation = self.get_object()
        return Response({
            'id': generation.id,
            'status': generation.status,
            'created_at': generation.created_at,
            'updated_at': generation.updated_at,
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def result(self, request, pk=None):
        """GET /api/generation/:generationId/result - Get generation result"""
        generation = self.get_object()
        if generation.status == 'completed' and generation.recipe:
            from .serializers import RecipeDetailSerializer
            return Response(RecipeDetailSerializer(generation.recipe).data)
        elif generation.status == 'failed':
            return Response({
                'error': generation.error_message or 'Generation failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'status': generation.status,
                'message': 'Generation is still in progress'
            }, status=status.HTTP_202_ACCEPTED)
