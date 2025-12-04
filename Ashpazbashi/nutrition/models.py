from django.db import models
from recipes.models import Recipe
from ingredients.models import Ingredient


class Nutrition(models.Model):
    """Nutrition information for recipes"""
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='nutrition',
        null=True,
        blank=True
    )
    calories = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    protein = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="in grams")
    carbohydrates = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="in grams")
    fat = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="in grams")
    fiber = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="in grams")
    sugar = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="in grams")
    sodium = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="in milligrams")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'nutrition'
        verbose_name = 'Nutrition'
        verbose_name_plural = 'Nutrition'
    
    def __str__(self):
        if self.recipe:
            return f"Nutrition for {self.recipe.title}"
        return f"Nutrition {self.id}"


class IngredientNutrition(models.Model):
    """Nutrition information for individual ingredients"""
    ingredient = models.OneToOneField(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='nutrition'
    )
    calories_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    protein_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    carbohydrates_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    fat_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    fiber_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    sugar_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    sodium_per_100g = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ingredient_nutrition'
        verbose_name = 'Ingredient Nutrition'
        verbose_name_plural = 'Ingredient Nutrition'
    
    def __str__(self):
        return f"Nutrition for {self.ingredient.name}"
