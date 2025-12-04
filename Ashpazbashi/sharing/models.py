import uuid
from django.db import models
from django.conf import settings
from recipes.models import Recipe


class RecipeShare(models.Model):
    """Share recipes with unique share IDs"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='shares')
    share_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_recipes'
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recipe_shares'
        verbose_name = 'Recipe Share'
        verbose_name_plural = 'Recipe Shares'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Share {self.share_id} for {self.recipe.title}"
