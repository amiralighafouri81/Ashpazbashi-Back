from django.db import models
from django.conf import settings
from recipes.models import Recipe


class RecipeHistory(models.Model):
    """Track user recipe viewing history"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipe_history')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='viewed_by')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recipe_history'
        verbose_name = 'Recipe History'
        verbose_name_plural = 'Recipe History'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} viewed {self.recipe.title} at {self.viewed_at}"
