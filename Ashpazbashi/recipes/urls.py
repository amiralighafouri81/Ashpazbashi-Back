from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, GenerationViewSet
from sharing.views import ShareViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'generation', GenerationViewSet, basename='generation')

urlpatterns = [
    path('', include(router.urls)),
    path('recipes/<int:recipe_id>/share/', ShareViewSet.as_view({'post': 'create_share'}), name='recipe-share'),
]
