from rest_framework import viewsets, permissions
from .models import Category, Tag, DietaryType
from .serializers import CategorySerializer, TagSerializer, DietaryTypeSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Category read operations"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Tag read operations"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class DietaryTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DietaryType read operations"""
    queryset = DietaryType.objects.all()
    serializer_class = DietaryTypeSerializer
    permission_classes = [permissions.AllowAny]
