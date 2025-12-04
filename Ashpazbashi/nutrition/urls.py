from django.urls import path
from .views import calculate_nutrition, ingredient_nutrition

urlpatterns = [
    path('nutrition/calculate/', calculate_nutrition, name='calculate-nutrition'),
    path('nutrition/ingredients/<int:ingredient_id>/', ingredient_nutrition, name='ingredient-nutrition'),
]


