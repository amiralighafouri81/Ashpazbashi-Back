from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random
from categories.models import Category, Tag, DietaryType
from ingredients.models import Ingredient, IngredientSubstitute
from recipes.models import Recipe, RecipeIngredient, RecipeRating, RecipeGeneration
from nutrition.models import Nutrition, IngredientNutrition
from bookmarks.models import Bookmark
from history.models import RecipeHistory
from users.models import UserProfile
from django.db import transaction

User = get_user_model()
fake = Faker("fa_IR")


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

        self._clear_existing_data()

        # Create categories
        self.stdout.write('Creating categories...')
        categories_data = [
            'خورش', 'کباب', 'پلو', 'دسر', 'سوپ', 'سالاد', 'پیش‌غذا', 'صبحانه', 'ناهار', 'شام',
            'میان‌وعده', 'نوشیدنی', 'کیک و شیرینی', 'گیاهی', 'دریایی', 'فوری', 'سنتی', 'بین‌الملل', 'فست‌فود', 'سلامت محور',
            'غذای خیابانی', 'ته‌دیگ', 'ساده و سریع'
        ]
        categories = []
        for cat_name in categories_data:
            cat, _ = Category.objects.get_or_create(name=cat_name)
            categories.append(cat)

        # Create tags
        self.stdout.write('Creating tags...')
        tags_data = [
            'سریع', 'آسان', 'رژیمی', 'کم‌چرب', 'کم‌نمک', 'پرپروتئین', 'بدون‌گلوتن', 'بدون‌لاکتوز', 'تند', 'شیرین',
            'خانگی', 'مجلسی', 'مناسب کودکان', 'فریزری', 'مناسب مهمانی', 'اقتصادی', 'بدون فر', 'یک‌قابلمه', 'پیک‌نیک', 'ناهار شرکتی',
            'کم‌کربوهیدرات', 'مناسب سفر'
        ]
        tags = []
        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)

        # Create dietary types
        self.stdout.write('Creating dietary types...')
        dietary_types_data = [
            ('وگان', '🌱'),
            ('وجترین', '🥬'),
            ('بدون‌گلوتن', '🌾'),
            ('بدون‌لاکتوز', '🥛'),
            ('کتو', '🥑'),
            ('پالئو', '🦴'),
            ('کم‌نمک', '🧂'),
            ('کم‌چرب', '🍋'),
            ('پرپروتئین', '🍗'),
            ('دیابتی', '🩺'),
            ('مناسب سالمندان', '👵'),
            ('مناسب کودکان', '🧒'),
            ('ورزشی', '🏋️'),
            ('بدون قند', '🚫🍭'),
            ('بدون آجیل', '🥜'),
            ('بدون سویا', '🚫🌱'),
            ('خام‌گیاه‌خواری', '🥒'),
            ('حساسیت لبنیات', '🚫🥛'),
            ('مناسب بارداری', '🤰'),
            ('کم‌کالری', '⚖️'),
        ]
        dietary_types = []
        for name, icon in dietary_types_data:
            dt, _ = DietaryType.objects.get_or_create(name=name, defaults={'icon': icon})
            dietary_types.append(dt)

        # Create ingredients
        self.stdout.write(f'Creating {num_ingredients} ingredients...')
        ingredients_data = [
            'آرد', 'شکر', 'نمک', 'فلفل سیاه', 'روغن زیتون', 'کره', 'تخم‌مرغ', 'شیر', 'مرغ', 'گوشت گوسفندی',
            'ماهی', 'برنج', 'ماکارونی', 'گوجه‌فرنگی', 'پیاز', 'سیر', 'هویج', 'سیب‌زمینی', 'فلفل دلمه‌ای', 'قارچ',
            'اسفناج', 'کاهو', 'پنیر فتا', 'ماست', 'نان بربری', 'لیمو ترش', 'آبلیمو', 'ریحان', 'پونه', 'آویشن',
            'رزماری', 'زیره', 'پاپریکا', 'دارچین', 'وانیل', 'شکلات تلخ', 'توت‌فرنگی', 'موز', 'سیب', 'پرتقال',
            'زعفران', 'گلاب', 'پسته', 'بادام', 'گردو', 'فندق', 'کشمش', 'خرما', 'نارگیل', 'کنجد',
            'عدس', 'نخود', 'لوبیا قرمز', 'لوبیا چیتی', 'ماش', 'جو پرک', 'بلغور گندم', 'ذرت شیرین', 'کینوا', 'سویا بافت‌دار',
            'ماست چکیده', 'خامه', 'پنیر پیتزا', 'پنیر گودا', 'پنیر پارمزان', 'تخم شنبلیله', 'شنبلیله خشک', 'زردچوبه', 'زنجبیل', 'هل سبز',
            'میخک', 'فلفل قرمز', 'ادویه کاری', 'ادویه پلویی', 'سماق', 'نعناع خشک', 'شوید خشک', 'خرفه', 'تربچه', 'کرفس',
            'کدو سبز', 'بادمجان', 'کلم بروکلی', 'گل‌کلم', 'کلم سفید', 'کلم قرمز', 'چغندر', 'خیار', 'کاهو رومی', 'کرفس ساقه',
            'کره بادام‌زمینی', 'عسل', 'مربای آلبالو', 'شیره انگور', 'شیره خرما', 'سرکه بالزامیک', 'سس سویا', 'سس کچاپ', 'سس مایونز', 'سس باربیکیو',
            'زعفران دم‌کرده', 'رب گوجه‌فرنگی', 'رب انار', 'تمر هندی', 'کشک'
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
                biography=fake.text(max_nb_chars=200) if random.choice([True, False]) else None,
            )
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'cooking_skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
                    'dietary_preferences': {'allergies': [], 'restrictions': []},
                    'favorite_cuisines': random.sample(['ایرانی', 'ترکی', 'هندی', 'ایتالیایی', 'مکزیکی', 'مدیترانه‌ای'], k=random.randint(1, 3))
                }
            )
            users.append(user)
        
        # Create recipes
        self.stdout.write(f'Creating {num_recipes} recipes...')
        difficulties = ['easy', 'medium', 'hard']
        recipes_data = [
            {
                'title': 'قرمه‌سبزی خانگی',
                'description': 'خورش اصیل ایرانی با سبزی تازه، لوبیا قرمز و گوشت گوسفندی نرم',
                'instructions': 'پیاز داغ بگیرید، گوشت را تفت دهید، سبزی را سرخ کنید، لوبیا و لیمو عمانی را افزوده و با آب بجوشانید تا جا بیفتد.',
            },
            {
                'title': 'قیمه نثار کرمانشاهی',
                'description': 'ترکیب خوش‌طعم گوشت، لپه و خلال بادام و پسته برای پذیرایی مجلسی',
                'instructions': 'پیاز را طلایی کنید، گوشت و لپه را تفت دهید، رب اضافه کنید، با آب بپزید و در انتها خلال‌ها و زعفران را اضافه کنید.',
            },
            {
                'title': 'زرشک‌پلو با مرغ زعفرانی',
                'description': 'مرغ مرینت‌شده زعفرانی با برنج کره‌ای و زرشک تفت‌داده',
                'instructions': 'مرغ را با پیاز، زعفران و ادویه تفت دهید، سس را غلیظ کنید، برنج آبکش را دم کنید و زرشک را با کره تفت دهید.',
            },
            {
                'title': 'مرغ ترش گیلانی',
                'description': 'مرغ تفت‌خورده با سبزی محلی، گردو و رب انار برای طعمی ملس',
                'instructions': 'مرغ را سرخ کنید، سبزی و گردو را جداگانه تفت دهید، با رب انار و آب بجوشانید تا غلیظ و جاافتاده شود.',
            },
            {
                'title': 'کشک بادمجان زغالی',
                'description': 'پیش‌غذای محبوب با بادمجان کبابی، سیر و نعناع داغ',
                'instructions': 'بادمجان را کبابی و له کنید، پیاز و سیر را تفت دهید، نعناع داغ آماده کنید، همه را با کشک مخلوط و سرو کنید.',
            },
            {
                'title': 'شامی ترش شمالی',
                'description': 'شامی لذیذ با گوشت چرخ‌کرده، لپه و سس رب انار',
                'instructions': 'لپه و گوشت را چرخ کنید، با پیاز و ادویه ورز دهید، سرخ کنید و در سس رب انار و گوجه بجوشانید.',
            },
            {
                'title': 'عدس‌پلو با گوشت قلقلی',
                'description': 'عدس‌پلوی مجلسی با کشمش و گوشت قلقلی معطر',
                'instructions': 'عدس را جدا بپزید، گوشت قلقلی را سرخ کنید، برنج را آبکش کرده لایه‌لایه با عدس، کشمش و گوشت دم کنید.',
            },
            {
                'title': 'خوراک بامیه با گوشت گوساله',
                'description': 'خوراک خانگی با بامیه سرخ‌شده، گوجه و ادویه‌ عربی',
                'instructions': 'بامیه را سرخ کنید، پیاز و گوشت را تفت دهید، رب و ادویه اضافه کنید، بامیه را در آخر اضافه کرده آهسته بپزید.',
            },
            {
                'title': 'پاستا پنه آلفردو با مرغ',
                'description': 'پاستای خامه‌ای با مرغ گریل‌شده، قارچ و پنیر پارمزان',
                'instructions': 'مرغ را گریل کنید، قارچ را تفت دهید، سس خامه و پارمزان بسازید، پاستا را بجوشانید و همه را مخلوط کنید.',
            },
            {
                'title': 'استیک فلفلی با سس قارچ',
                'description': 'فیله گوساله با کره سیر و سس قارچ خامه‌ای',
                'instructions': 'فیله را با کره و سیر سیر کنید، در تابه داغ سرخ کنید، قارچ و خامه را تفت دهید و سس را کنار استیک سرو کنید.',
            },
            {
                'title': 'سوپ جو کرمی',
                'description': 'سوپ مقوی با جو پرک، شیر، هویج و مرغ ریش‌ریش',
                'instructions': 'جو را بپزید، پیاز و هویج را تفت دهید، آب مرغ و شیر اضافه کنید، مرغ ریش‌ریش و جعفری را در انتها بریزید.',
            },
            {
                'title': 'سالاد شیرازی با آبغوره',
                'description': 'سالاد کلاسیک ایرانی با طعم تند و ترش آبغوره',
                'instructions': 'گوجه، خیار و پیاز را ریز خرد کنید، با آبغوره، نعناع خشک، نمک و فلفل مخلوط و خنک سرو کنید.',
            },
            {
                'title': 'کتلت سیب‌زمینی و گوشت',
                'description': 'کتلت خانگی ترد با سیب‌زمینی، گوشت و ادویه',
                'instructions': 'سیب‌زمینی پخته و گوشت چرخ‌کرده را با پیاز و ادویه مخلوط کنید، شکل دهید و در روغن کم سرخ کنید.',
            },
            {
                'title': 'اشکنه شنبلیله',
                'description': 'غذای ساده و سریع با سیب‌زمینی، تخم‌مرغ و شنبلیله خشک',
                'instructions': 'پیاز را تفت دهید، شنبلیله و سیب‌زمینی نگینی را اضافه کنید، آب بریزید و در انتها تخم‌مرغ را در آن بشکنید.',
            },
            {
                'title': 'کوفته‌برنجی زعفرانی',
                'description': 'کوفته‌های معطر با برنج، گوشت و سبزیجات معطر',
                'instructions': 'برنج نیم‌پز، گوشت و سبزی را با تخم‌مرغ ورز دهید، گرد کنید، در سس گوجه و زعفران آرام بپزید.',
            },
            {
                'title': 'کباب تابه‌ای با سماق',
                'description': 'کباب خانگی آبدار با سماق و گوجه سرخ‌شده',
                'instructions': 'گوشت چرخ‌کرده، پیاز و سماق را ورز دهید، در تابه پهن کنید، سرخ کنید و با گوجه و نان سرو کنید.',
            },
            {
                'title': 'خورش کدو حلوایی',
                'description': 'خورش گرم با کدو حلوایی، لوبیا و عطر دارچین',
                'instructions': 'پیاز و گوشت را تفت دهید، کدو حلوایی و لوبیا اضافه کنید، با دارچین و رب بپزید تا جا بیفتد.',
            },
            {
                'title': 'سمبوسه سبزیجات تند',
                'description': 'خمیر سمبوسه با پرِ سیب‌زمینی، نخود و ادویه کاری',
                'instructions': 'سیب‌زمینی و نخود را با پیاز و ادویه کاری تفت دهید، خمیر را پر کنید، ببندید و در روغن سرخ کنید.',
            },
            {
                'title': 'پنکیک موز و عسل',
                'description': 'صبحانه شیرین با موز رسیده، عسل و دارچین',
                'instructions': 'موز له‌شده، تخم‌مرغ و آرد را مخلوط کنید، در تابه چرب سرخ کنید و با عسل و دارچین سرو کنید.',
            },
            {
                'title': 'خوراک لوبیا چیتی با سبزی معطر',
                'description': 'خوراک خانگی با لوبیا، سیر، جعفری و رب گوجه',
                'instructions': 'لوبیا را بپزید، پیاز و سیر را تفت دهید، رب و جعفری را اضافه کنید، لوبیا را بیفزایید و آرام بجوشانید.',
            },
        ]
        for i in range(num_recipes):
            base = recipes_data[i % len(recipes_data)]
            recipe = Recipe.objects.create(
                title=base['title'],
                description=base['description'],
                instructions=base['instructions'],
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

    def _clear_existing_data(self):
        """Delete existing records while keeping users."""
        self.stdout.write('Cleaning existing data (keeping users)...')
        with transaction.atomic():
            Bookmark.objects.all().delete()
            RecipeHistory.objects.all().delete()
            RecipeRating.objects.all().delete()
            RecipeIngredient.objects.all().delete()
            Nutrition.objects.all().delete()
            RecipeGeneration.objects.all().delete()
            Recipe.objects.all().delete()
            IngredientSubstitute.objects.all().delete()
            IngredientNutrition.objects.all().delete()
            Ingredient.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()
            DietaryType.objects.all().delete()
