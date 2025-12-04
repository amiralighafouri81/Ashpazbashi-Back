from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TagViewSet, DietaryTypeViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'dietary-types', DietaryTypeViewSet, basename='dietary-type')

urlpatterns = [
    path('', include(router.urls)),
]


