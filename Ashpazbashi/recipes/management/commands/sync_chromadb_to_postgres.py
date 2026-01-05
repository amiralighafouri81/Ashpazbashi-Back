"""
Django management command to sync recipe data from ChromaDB/JSONL to PostgreSQL.

This command reads recipe data from either:
1. ChromaDB API (via /search endpoint)
2. JSONL file (direct file reading)

And syncs it to PostgreSQL Django models.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from recipes.models import Recipe, RecipeIngredient
from ingredients.models import Ingredient
from categories.models import Category

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync recipe data from ChromaDB/JSONL to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['jsonl', 'chromadb'],
            default='jsonl',
            help='Data source: jsonl (read from file) or chromadb (read from API)'
        )
        parser.add_argument(
            '--jsonl-path',
            type=str,
            help='Path to JSONL file (default: ../../data-insertion/Ashpazyar-data.jsonl)'
        )
        parser.add_argument(
            '--chromadb-url',
            type=str,
            default='http://localhost:8324',
            help='ChromaDB API URL (default: http://localhost:8324)'
        )
        parser.add_argument(
            '--chromadb-token',
            type=str,
            help='ChromaDB access token (or set CHROMA_ACCESS_TOKEN env var)'
        )
        parser.add_argument(
            '--author-username',
            type=str,
            help='Username of the author for recipes (default: creates/uses "system" user)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually saving to database'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing recipes if they already exist (by title)'
        )

    def handle(self, *args, **options):
        source = options['source']
        dry_run = options['dry_run']
        update_existing = options['update_existing']

        self.stdout.write(self.style.SUCCESS(f'Starting sync from {source}...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Check if migrations are needed
        try:
            from django.core.management import call_command
            from django.db import connection
            # Quick check: try to access a table
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users LIMIT 1")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    '\n❌ Database schema is out of sync with models!\n'
                    'Please run migrations first:\n'
                    '  python manage.py migrate\n\n'
                    f'Error: {e}'
                )
            )
            raise CommandError('Database migrations required. Run: python manage.py migrate')

        # Get or create author user
        try:
            author = self._get_or_create_author(options.get('author_username'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ Failed to get/create author user: {e}\n'
                    'This might indicate missing migrations. Try running:\n'
                    '  python manage.py migrate\n'
                )
            )
            raise

        # Load recipes based on source
        if source == 'jsonl':
            recipes_data = self._load_from_jsonl(options.get('jsonl_path'))
        else:
            recipes_data = self._load_from_chromadb(
                options['chromadb_url'],
                options.get('chromadb_token') or os.getenv('CHROMA_ACCESS_TOKEN')
            )

        if not recipes_data:
            raise CommandError('No recipes found to sync')

        self.stdout.write(f'Found {len(recipes_data)} recipes to sync')

        # Sync recipes
        synced_count = 0
        updated_count = 0
        created_count = 0
        error_count = 0

        for recipe_data in recipes_data:
            try:
                if dry_run:
                    self.stdout.write(f'[DRY RUN] Would sync: {recipe_data.get("foodname", "Unknown")}')
                    synced_count += 1
                    continue

                with transaction.atomic():
                    recipe, created = self._sync_recipe(recipe_data, author, update_existing)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    synced_count += 1

                    if synced_count % 10 == 0:
                        self.stdout.write(f'Processed {synced_count}/{len(recipes_data)} recipes...')

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error syncing recipe "{recipe_data.get("foodname", "Unknown")}": {e}')
                )
                if not dry_run:
                    continue

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Sync Summary:'))
        self.stdout.write(f'  Total recipes processed: {synced_count}')
        if not dry_run:
            self.stdout.write(f'  Created: {created_count}')
            self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(self.style.SUCCESS('='*50))

    def _fix_user_table_schema(self):
        """Add missing columns to users table if they don't exist"""
        from django.db import connection
        
        columns_to_add = [
            ('student_number', 'VARCHAR(50) NULL'),
            ('role', 'VARCHAR(20) NOT NULL DEFAULT \'user\''),
            ('biography', 'TEXT NULL'),
            ('profile_picture', 'VARCHAR(100) NULL'),
            ('created_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        try:
            with connection.cursor() as cursor:
                # Get existing columns
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users'
                """)
                existing_columns = {row[0] for row in cursor.fetchall()}
                
                # Add missing columns
                for column_name, column_def in columns_to_add:
                    if column_name not in existing_columns:
                        self.stdout.write(self.style.WARNING(f'Adding missing column: {column_name}...'))
                        try:
                            cursor.execute(f"""
                                ALTER TABLE users 
                                ADD COLUMN {column_name} {column_def}
                            """)
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Added {column_name}'))
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'  ✗ Could not add {column_name}: {e}')
                            )
                
                # Add unique constraint for student_number if it doesn't exist
                if 'student_number' not in existing_columns:
                    try:
                        cursor.execute("""
                            CREATE UNIQUE INDEX IF NOT EXISTS users_student_number_unique 
                            ON users(student_number) 
                            WHERE student_number IS NOT NULL
                        """)
                    except Exception:
                        pass  # Index might already exist or constraint issue
                        
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not fix user table schema: {e}')
            )

    def _get_or_create_author(self, username: Optional[str] = None) -> User:
        """Get or create a system user as recipe author"""
        from django.db import connection
        
        # Fix schema first
        self._fix_user_table_schema()
        
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'User "{username}" not found. Please create it first.')

        # Create or get system user using raw SQL to avoid ORM issues
        try:
            with connection.cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT id FROM users WHERE username = %s", ['system'])
                result = cursor.fetchone()
                
                if result:
                    # User exists, get it via ORM
                    return User.objects.get(id=result[0])
                
                # User doesn't exist, create it
                from django.utils import timezone
                from django.contrib.auth.hashers import make_password
                
                self.stdout.write(self.style.WARNING('Creating system user...'))
                cursor.execute("""
                    INSERT INTO users (
                        username, email, first_name, last_name, 
                        is_staff, is_superuser, is_active, date_joined, 
                        password, role, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    'system', 'system@ashpazyar.local', 'System', 'User',
                    False, False, True, timezone.now(),
                    make_password(None),  # Unusable password
                    'user',  # Default role
                    timezone.now(), timezone.now()
                ])
                user_id = cursor.fetchone()[0]
                
                # Get the user via ORM
                author = User.objects.get(id=user_id)
                self.stdout.write(self.style.SUCCESS('Created system user for recipes'))
                return author
                
        except Exception as e:
            # Fallback: try ORM method
            self.stdout.write(
                self.style.WARNING(f'Raw SQL method failed: {e}. Trying ORM method...')
            )
            try:
                author = User.objects.create(
                    username='system',
                    email='system@ashpazyar.local',
                    first_name='System',
                    last_name='User',
                    is_staff=False,
                    is_superuser=False,
                    role='user',
                )
                author.set_unusable_password()
                author.save()
                self.stdout.write(self.style.SUCCESS('Created system user for recipes'))
                return author
            except Exception as orm_error:
                raise CommandError(
                    f'Failed to create system user. Database schema may be incomplete.\n'
                    f'Error: {orm_error}\n'
                    f'Please run: python manage.py migrate'
                )

    def _load_from_jsonl(self, jsonl_path: Optional[str] = None) -> List[Dict]:
        """Load recipes from JSONL file"""
        if not jsonl_path:
            # Default path relative to management command
            base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            jsonl_path = base_dir / 'data-insertion' / 'Ashpazyar-data.jsonl'

        jsonl_path = Path(jsonl_path)
        if not jsonl_path.exists():
            raise CommandError(f'JSONL file not found: {jsonl_path}')

        self.stdout.write(f'Reading from JSONL: {jsonl_path}')
        recipes = []

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    recipe = json.loads(line)
                    recipes.append(recipe)
                except json.JSONDecodeError as e:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping invalid JSON on line {line_num}: {e}')
                    )

        return recipes

    def _load_from_chromadb(self, chromadb_url: str, token: Optional[str]) -> List[Dict]:
        """Load recipes from ChromaDB API"""
        try:
            import requests
        except ImportError:
            raise CommandError(
                'requests module is required for ChromaDB source. '
                'Install it with: pip install requests'
            )

        if not token:
            raise CommandError('ChromaDB token required. Use --chromadb-token or set CHROMA_ACCESS_TOKEN env var')

        self.stdout.write(f'Fetching from ChromaDB: {chromadb_url}')

        # Get all recipes (empty query returns all)
        url = f'{chromadb_url}/search'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'query': '',
            'limit': 1000  # Adjust based on your data size
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            results = response.json()

            # Convert ChromaDB format to our format
            recipes = []
            for item in results:
                recipe = {
                    'foodname': item.get('foodname', ''),
                    'ingredients': item.get('ingredients', {}),
                    'canonical': item.get('canonical', []),
                    'recipe': self._extract_recipe_steps(item.get('recipe', '')),
                    'calory': item.get('calory', ''),
                    'taken_time': item.get('taken_time', []),
                    'images': item.get('images', []),
                    'questions': item.get('questions', {}),
                    'index': item.get('index', 0.0)
                }
                recipes.append(recipe)

            return recipes

        except requests.exceptions.RequestException as e:
            raise CommandError(f'Failed to fetch from ChromaDB: {e}')

    def _extract_recipe_steps(self, recipe_content: str) -> List[str]:
        """Extract recipe steps from page_content string"""
        if isinstance(recipe_content, list):
            return recipe_content
        
        # Try to extract steps from text
        # This is a simple approach - adjust based on your actual format
        steps = recipe_content.split('\n')
        return [s.strip() for s in steps if s.strip()]

    def _parse_time(self, taken_time: List[str]) -> tuple[int, int]:
        """Parse cooking time from taken_time list"""
        prep_time = 15  # Default
        cook_time = 30  # Default

        if taken_time and len(taken_time) > 0:
            time_str = taken_time[0]
            # Try to extract numbers (simple approach)
            numbers = re.findall(r'\d+', time_str)
            if numbers:
                total_minutes = int(numbers[0])
                # Split prep and cook time (simple heuristic)
                prep_time = max(5, total_minutes // 3)
                cook_time = max(10, total_minutes - prep_time)

        return prep_time, cook_time

    def _determine_difficulty(self, recipe_steps: List[str], ingredient_count: int) -> str:
        """Determine recipe difficulty based on steps and ingredients"""
        step_count = len(recipe_steps)
        
        if step_count <= 3 and ingredient_count <= 5:
            return 'easy'
        elif step_count <= 6 and ingredient_count <= 10:
            return 'medium'
        else:
            return 'hard'

    @transaction.atomic
    def _sync_recipe(self, recipe_data: Dict, author: User, update_existing: bool) -> tuple[Recipe, bool]:
        """Sync a single recipe to PostgreSQL"""
        foodname = recipe_data.get('foodname', '').strip()
        if not foodname:
            raise ValueError('Recipe foodname is required')

        # Check if recipe already exists
        existing_recipe = None
        if update_existing:
            existing_recipe = Recipe.objects.filter(title=foodname, author=author).first()

        # Prepare recipe data
        recipe_steps = recipe_data.get('recipe', [])
        if isinstance(recipe_steps, str):
            recipe_steps = [recipe_steps]

        instructions = '\n'.join(recipe_steps)
        description = recipe_steps[0] if recipe_steps else f'Delicious {foodname} recipe'

        prep_time, cook_time = self._parse_time(recipe_data.get('taken_time', []))
        ingredient_count = len(recipe_data.get('canonical', []))
        difficulty = self._determine_difficulty(recipe_steps, ingredient_count)

        # Get first image URL if available
        images = recipe_data.get('images', [])
        image_url = images[0] if images else None

        # Create or update recipe
        if existing_recipe:
            recipe = existing_recipe
            recipe.description = description
            recipe.instructions = instructions
            recipe.prep_time = prep_time
            recipe.cook_time = cook_time
            recipe.difficulty = difficulty
            recipe.servings = 4  # Default
            recipe.save()
            created = False
        else:
            recipe = Recipe.objects.create(
                title=foodname,
                description=description,
                instructions=instructions,
                prep_time=prep_time,
                cook_time=cook_time,
                servings=4,  # Default serving size
                difficulty=difficulty,
                author=author,
                is_public=True
            )
            created = True

        # Sync ingredients
        self._sync_recipe_ingredients(recipe, recipe_data)

        return recipe, created

    def _sync_recipe_ingredients(self, recipe: Recipe, recipe_data: Dict):
        """Sync ingredients for a recipe"""
        # Clear existing ingredients if updating
        RecipeIngredient.objects.filter(recipe=recipe).delete()

        ingredients_dict = recipe_data.get('ingredients', {})
        canonical_list = recipe_data.get('canonical', [])

        # Use canonical list as primary source, fallback to ingredients dict keys
        ingredient_names = canonical_list if canonical_list else list(ingredients_dict.keys())

        for order, ingredient_name in enumerate(ingredient_names, start=1):
            ingredient_name = ingredient_name.strip()
            if not ingredient_name:
                continue

            # Get or create ingredient
            ingredient, _ = Ingredient.objects.get_or_create(
                name=ingredient_name,
                defaults={'unit': 'g'}
            )

            # Get quantity from ingredients dict
            quantity = ingredients_dict.get(ingredient_name, 'به میزان لازم')
            if not quantity or quantity.strip() == '':
                quantity = 'به میزان لازم'

            # Create recipe ingredient relationship
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                quantity=quantity[:100],  # Ensure it fits in CharField
                order=order
            )

