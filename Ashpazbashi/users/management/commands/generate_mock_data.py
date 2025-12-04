from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random
from categories.models import Category, Tag, DietaryType
from ingredients.models import Ingredient, IngredientSubstitute
from recipes.models import Recipe, RecipeIngredient, RecipeRating
from nutrition.models import Nutrition, IngredientNutrition
from bookmarks.models import Bookmark
from history.models import RecipeHistory
from users.models import UserProfile

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generate mock data for AshpazYar application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--recipes',
            type=int,
            default=50,
            help='Number of recipes to create'
        )
        parser.add_argument(
            '--ingredients',
            type=int,
            default=100,
            help='Number of ingredients to create'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting mock data generation...'))
        
        num_users = options['users']
        num_recipes = options['recipes']
        num_ingredients = options['ingredients']
        
        # Create categories
        self.stdout.write('Creating categories...')
        categories_data = [
            'Main Course', 'Appetizer', 'Dessert', 'Salad', 'Soup',
            'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Beverage'
        ]
        categories = []
        for cat_name in categories_data:
            cat, _ = Category.objects.get_or_create(name=cat_name)
            categories.append(cat)
        
        # Create tags
        self.stdout.write('Creating tags...')
        tags_data = [
            'quick', 'easy', 'healthy', 'vegetarian', 'vegan', 'gluten-free',
            'dairy-free', 'spicy', 'sweet', 'savory', 'comfort-food', 'low-carb'
        ]
        tags = []
        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
        
        # Create dietary types
        self.stdout.write('Creating dietary types...')
        dietary_types_data = [
            ('Vegan', '🌱'),
            ('Vegetarian', '🥬'),
            ('Gluten-Free', '🌾'),
            ('Dairy-Free', '🥛'),
            ('Keto', '🥑'),
            ('Paleo', '🦴'),
        ]
        dietary_types = []
        for name, icon in dietary_types_data:
            dt, _ = DietaryType.objects.get_or_create(name=name, defaults={'icon': icon})
            dietary_types.append(dt)
        
        # Create ingredients
        self.stdout.write(f'Creating {num_ingredients} ingredients...')
        ingredients_data = [
            'Flour', 'Sugar', 'Salt', 'Pepper', 'Olive Oil', 'Butter', 'Eggs',
            'Milk', 'Chicken', 'Beef', 'Fish', 'Rice', 'Pasta', 'Tomatoes',
            'Onions', 'Garlic', 'Carrots', 'Potatoes', 'Bell Peppers', 'Mushrooms',
            'Spinach', 'Lettuce', 'Cheese', 'Yogurt', 'Bread', 'Lemon', 'Lime',
            'Basil', 'Oregano', 'Thyme', 'Rosemary', 'Cumin', 'Paprika', 'Cinnamon',
            'Vanilla', 'Chocolate', 'Strawberries', 'Bananas', 'Apples', 'Oranges',
        ]
        ingredients = []
        for ing_name in ingredients_data[:num_ingredients]:
            ing, _ = Ingredient.objects.get_or_create(
                name=ing_name,
                defaults={
                    'description': fake.text(max_nb_chars=100),
                    'unit': random.choice(['g', 'ml', 'cup', 'tsp', 'tbsp', 'piece'])
                }
            )
            ingredients.append(ing)
        
        # Create ingredient nutrition data
        self.stdout.write('Creating ingredient nutrition data...')
        for ingredient in ingredients[:30]:  # Add nutrition for first 30 ingredients
            IngredientNutrition.objects.get_or_create(
                ingredient=ingredient,
                defaults={
                    'calories_per_100g': random.uniform(50, 500),
                    'protein_per_100g': random.uniform(0, 30),
                    'carbohydrates_per_100g': random.uniform(0, 80),
                    'fat_per_100g': random.uniform(0, 40),
                    'fiber_per_100g': random.uniform(0, 10),
                    'sugar_per_100g': random.uniform(0, 50),
                    'sodium_per_100g': random.uniform(0, 2000),
                }
            )
        
        # Create ingredient substitutes
        self.stdout.write('Creating ingredient substitutes...')
        for i in range(min(20, len(ingredients) // 2)):
            if len(ingredients) > i * 2 + 1:
                IngredientSubstitute.objects.get_or_create(
                    original_ingredient=ingredients[i * 2],
                    substitute_ingredient=ingredients[i * 2 + 1],
                    defaults={
                        'substitution_ratio': '1:1',
                        'notes': fake.text(max_nb_chars=50)
                    }
                )
        
        # Create users
        self.stdout.write(f'Creating {num_users} users...')
        users = []
        for i in range(num_users):
            user = User.objects.create_user(
                username=fake.user_name() + str(i),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password='password123',
                student_number=fake.numerify(text='#######') if random.choice([True, False]) else None,
                biography=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
            )
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'cooking_skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
                    'dietary_preferences': {'allergies': [], 'restrictions': []},
                    'favorite_cuisines': random.sample(['Italian', 'Mexican', 'Asian', 'American'], k=random.randint(1, 3))
                }
            )
            users.append(user)
        
        # Create recipes
        self.stdout.write(f'Creating {num_recipes} recipes...')
        difficulties = ['easy', 'medium', 'hard']
        for i in range(num_recipes):
            recipe = Recipe.objects.create(
                title=fake.sentence(nb_words=4).rstrip('.'),
                description=fake.text(max_nb_chars=300),
                instructions=fake.text(max_nb_chars=1000),
                prep_time=random.randint(10, 120),
                cook_time=random.randint(15, 180),
                servings=random.randint(1, 8),
                difficulty=random.choice(difficulties),
                author=random.choice(users),
                category=random.choice(categories) if categories else None,
                is_public=random.choice([True, True, True, False]),  # 75% public
            )
            
            # Add tags
            recipe.tags.set(random.sample(tags, k=random.randint(1, 4)))
            
            # Add dietary types
            recipe.dietary_types.set(random.sample(dietary_types, k=random.randint(0, 3)))
            
            # Add ingredients
            recipe_ingredients = random.sample(ingredients, k=random.randint(3, 10))
            for idx, ing in enumerate(recipe_ingredients):
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ing,
                    quantity=f"{random.randint(1, 5)} {ing.unit}",
                    order=idx
                )
            
            # Create nutrition for recipe
            Nutrition.objects.create(
                recipe=recipe,
                calories=random.uniform(100, 800),
                protein=random.uniform(5, 50),
                carbohydrates=random.uniform(10, 100),
                fat=random.uniform(2, 40),
                fiber=random.uniform(0, 15),
                sugar=random.uniform(0, 50),
                sodium=random.uniform(100, 2000),
            )
            
            # Add ratings
            num_ratings = random.randint(0, 15)
            rated_users = set()
            for _ in range(num_ratings):
                user = random.choice(users)
                # Ensure each user only rates once per recipe
                if user.id not in rated_users:
                    RecipeRating.objects.get_or_create(
                        recipe=recipe,
                        user=user,
                        defaults={
                            'rating': random.randint(1, 5),
                            'comment': fake.text(max_nb_chars=100) if random.choice([True, False]) else ''
                        }
                    )
                    rated_users.add(user.id)
            
            # Update recipe rating stats
            from django.db.models import Avg
            ratings = RecipeRating.objects.filter(recipe=recipe)
            if ratings.exists():
                recipe.average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
                recipe.ratings_count = ratings.count()
                recipe.save()
        
        # Create bookmarks
        self.stdout.write('Creating bookmarks...')
        for _ in range(min(50, num_recipes * 2)):
            user = random.choice(users)
            recipe = random.choice(Recipe.objects.all())
            Bookmark.objects.get_or_create(user=user, recipe=recipe)
        
        # Create history
        self.stdout.write('Creating history...')
        for _ in range(min(100, num_recipes * 3)):
            user = random.choice(users)
            recipe = random.choice(Recipe.objects.all())
            RecipeHistory.objects.create(user=user, recipe=recipe)
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully generated mock data:'))
        self.stdout.write(f'  - {User.objects.count()} users')
        self.stdout.write(f'  - {Category.objects.count()} categories')
        self.stdout.write(f'  - {Tag.objects.count()} tags')
        self.stdout.write(f'  - {DietaryType.objects.count()} dietary types')
        self.stdout.write(f'  - {Ingredient.objects.count()} ingredients')
        self.stdout.write(f'  - {Recipe.objects.count()} recipes')
        self.stdout.write(f'  - {Bookmark.objects.count()} bookmarks')
        self.stdout.write(f'  - {RecipeHistory.objects.count()} history entries')

