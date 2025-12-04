from django.db import models
from django.conf import settings
from ingredients.models import Ingredient
from categories.models import Category, Tag, DietaryType


class Recipe(models.Model):
    """Main Recipe model"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    prep_time = models.IntegerField(help_text="Preparation time in minutes")
    cook_time = models.IntegerField(help_text="Cooking time in minutes")
    servings = models.IntegerField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    
    # Relationships
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='recipes')
    dietary_types = models.ManyToManyField(DietaryType, blank=True, related_name='recipes')
    
    # Metadata
    views_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    ratings_count = models.IntegerField(default=0)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipes'
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    """Many-to-many relationship between Recipe and Ingredient with quantity"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='recipe_ingredients')
    quantity = models.CharField(max_length=100, help_text="e.g., '2 cups', '500g', '1/2 tsp'")
    notes = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Order in ingredient list")
    
    class Meta:
        db_table = 'recipe_ingredients'
        verbose_name = 'Recipe Ingredient'
        verbose_name_plural = 'Recipe Ingredients'
        ordering = ['order', 'ingredient__name']
        unique_together = ['recipe', 'ingredient']
    
    def __str__(self):
        return f"{self.recipe.title} - {self.ingredient.name}"


class RecipeRating(models.Model):
    """User ratings for recipes"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipe_ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Rating from 1 to 5")
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipe_ratings'
        verbose_name = 'Recipe Rating'
        verbose_name_plural = 'Recipe Ratings'
        unique_together = ['recipe', 'user']
    
    def __str__(self):
        return f"{self.user.username} rated {self.recipe.title} - {self.rating} stars"


class RecipeGeneration(models.Model):
    """Track AI recipe generation requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generations')
    prompt = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation'
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recipe_generations'
        verbose_name = 'Recipe Generation'
        verbose_name_plural = 'Recipe Generations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Generation {self.id} - {self.status}"
