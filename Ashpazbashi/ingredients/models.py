from django.db import models


class Ingredient(models.Model):
    """Ingredients used in recipes"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='ingredients/', blank=True, null=True)
    unit = models.CharField(max_length=20, default='g')  # Default unit (g, ml, cup, etc.)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ingredients'
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class IngredientSubstitute(models.Model):
    """Substitute relationships between ingredients"""
    original_ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='substitutes'
    )
    substitute_ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='substituted_in'
    )
    substitution_ratio = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., '1:1' or '1 cup:1 cup'"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ingredient_substitutes'
        verbose_name = 'Ingredient Substitute'
        verbose_name_plural = 'Ingredient Substitutes'
        unique_together = ['original_ingredient', 'substitute_ingredient']
    
    def __str__(self):
        return f"{self.original_ingredient.name} -> {self.substitute_ingredient.name}"
