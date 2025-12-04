from django.db import models


class Category(models.Model):
    """Recipe categories (e.g., Main Course, Dessert, Appetizer)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Recipe tags for flexible categorization"""
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DietaryType(models.Model):
    """Dietary types (e.g., Vegan, Vegetarian, Gluten-Free)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # For icon class or emoji
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dietary_types'
        verbose_name = 'Dietary Type'
        verbose_name_plural = 'Dietary Types'
        ordering = ['name']
    
    def __str__(self):
        return self.name
