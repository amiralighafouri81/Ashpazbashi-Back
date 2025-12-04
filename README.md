# AshpazYar Backend API

Django REST Framework backend for the AshpazYar cooking application.

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 12+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`: `cp .env.example .env` (or create `.env` manually)
   - Edit `.env` and update the following:
     - `SECRET_KEY`: Generate a new secret key (or keep default for development)
     - `DB_PASSWORD`: Your PostgreSQL password
     - `CORS_ALLOWED_ORIGINS`: Your frontend URL (default: `http://localhost:3000`)

3. Configure PostgreSQL database:
   - Create a database named `ashpazyar_db` (or use the name in your `.env` file)
   - Database credentials are now read from `.env` file

4. Run migrations:
```bash
cd Ashpazbashi
python manage.py migrate
```

4. Create superuser:
```bash
python manage.py createsuperuser
```

5. Generate mock data (optional):
```bash
python manage.py generate_mock_data --users 20 --recipes 50 --ingredients 100
```

6. Run development server:
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication

#### Register User
- **POST** `/auth/users/`
- **Body:**
```json
{
  "username": "user123",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "student_number": "1234567",
  "password": "password123",
  "password_confirmation": "password123"
}
```

#### Login
- **POST** `/auth/jwt/create/`
- **Body:**
```json
{
  "username": "user123",
  "password": "password123"
}
```
- **Response:** Returns `access` and `refresh` tokens

#### Refresh Token
- **POST** `/auth/jwt/refresh/`
- **Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

#### Get Current User
- **GET** `/auth/users/me/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Update Current User
- **PUT** `/auth/users/me/`
- **Headers:** `Authorization: Bearer <access_token>`

### User Profile

#### Get User Profile
- **GET** `/api/users/profile/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Update User Profile
- **PUT** `/api/users/profile/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Get Dietary Preferences
- **GET** `/api/users/dietary-preferences/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Update Dietary Preferences
- **PUT** `/api/users/dietary-preferences/`
- **Body:**
```json
{
  "dietary_preferences": {"allergies": ["nuts"], "restrictions": []},
  "favorite_cuisines": ["Italian", "Mexican"],
  "cooking_skill_level": "intermediate"
}
```

### Recipes

#### List Recipes
- **GET** `/api/recipes/recipes/`
- **Query Parameters:**
  - `category` - Filter by category ID
  - `difficulty` - Filter by difficulty (easy, medium, hard)
  - `tags` - Filter by tag IDs
  - `dietary_types` - Filter by dietary type IDs
  - `author` - Filter by author ID
  - `search` - Search in title, description, tags
  - `ordering` - Order by: created_at, average_rating, views_count, prep_time, cook_time
  - `page` - Page number for pagination

#### Get Recipe Detail
- **GET** `/api/recipes/recipes/{id}/`
- Automatically tracks view history for authenticated users

#### Create Recipe
- **POST** `/api/recipes/recipes/`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "title": "Delicious Pasta",
  "description": "A tasty pasta recipe",
  "instructions": "Step by step instructions...",
  "prep_time": 15,
  "cook_time": 30,
  "servings": 4,
  "difficulty": "medium",
  "category_id": 1,
  "tag_ids": [1, 2],
  "dietary_type_ids": [1],
  "is_public": true
}
```

#### Update Recipe
- **PUT/PATCH** `/api/recipes/recipes/{id}/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Delete Recipe
- **DELETE** `/api/recipes/recipes/{id}/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Generate Recipe (AI)
- **POST** `/api/recipes/recipes/generate/`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "prompt": "Create a vegan pasta recipe"
}
```

#### Find Recipes by Ingredients
- **POST** `/api/recipes/recipes/by-ingredients/`
- **Body:**
```json
{
  "ingredient_ids": [1, 2, 3, 4]
}
```

#### Get Similar Recipes
- **GET** `/api/recipes/recipes/{id}/similar/`

#### Rate Recipe
- **POST** `/api/recipes/recipes/{id}/rate/`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "rating": 5,
  "comment": "Great recipe!"
}
```

### Ingredients

#### List Ingredients
- **GET** `/api/ingredients/ingredients/`
- **Query Parameters:**
  - `search` - Search by name
  - `ordering` - Order by name, created_at

#### Search Ingredients
- **GET** `/api/ingredients/ingredients/search/?q=chicken`

#### Get Ingredient Substitutes
- **GET** `/api/ingredients/ingredients/{id}/substitutes/`

#### Suggest Substitutes
- **POST** `/api/ingredients/ingredients/substitute/`
- **Body:**
```json
{
  "ingredient_ids": [1, 2, 3]
}
```

### Nutrition

#### Calculate Nutrition
- **POST** `/api/nutrition/calculate/`
- **Body (Option 1 - Recipe):**
```json
{
  "recipe_id": 1
}
```
- **Body (Option 2 - Ingredients):**
```json
{
  "ingredients": [
    {"ingredient_id": 1, "quantity": "200g"},
    {"ingredient_id": 2, "quantity": "1 cup"}
  ]
}
```

#### Get Ingredient Nutrition
- **GET** `/api/nutrition/ingredients/{id}/`

### Bookmarks

#### List Bookmarks
- **GET** `/api/bookmarks/bookmarks/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Create Bookmark
- **POST** `/api/bookmarks/bookmarks/`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**
```json
{
  "recipe_id": 1
}
```

#### Delete Bookmark
- **DELETE** `/api/bookmarks/bookmarks/{id}/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Check if Bookmarked
- **GET** `/api/bookmarks/bookmarks/check/{recipe_id}/`
- **Headers:** `Authorization: Bearer <access_token>`

### History

#### List History
- **GET** `/api/history/history/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Add to History
- **POST** `/api/history/history/{recipe_id}/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Clear History
- **DELETE** `/api/history/history/clear/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Delete History Entry
- **DELETE** `/api/history/history/{id}/`
- **Headers:** `Authorization: Bearer <access_token>`

### Categories, Tags, Dietary Types

#### List Categories
- **GET** `/api/categories/categories/`

#### List Tags
- **GET** `/api/categories/tags/`

#### List Dietary Types
- **GET** `/api/categories/dietary-types/`

### Recipe Generation

#### Get Generation Status
- **GET** `/api/recipes/generation/{id}/status/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Get Generation Result
- **GET** `/api/recipes/generation/{id}/result/`
- **Headers:** `Authorization: Bearer <access_token>`

### Sharing

#### Create Share Link
- **POST** `/api/recipes/recipes/{recipe_id}/share/`
- **Headers:** `Authorization: Bearer <access_token>`

#### Get Shared Recipe
- **GET** `/api/share/share/{share_id}/`

## Models

### User
- Custom user model extending AbstractUser
- Fields: username, email, first_name, last_name, student_number, role, biography, profile_picture

### Recipe
- Main recipe model with full CRUD support
- Fields: title, description, instructions, prep_time, cook_time, servings, difficulty, image, author, category, tags, dietary_types, views_count, average_rating, ratings_count

### Ingredient
- Ingredient catalog
- Fields: name, description, image, unit

### Category, Tag, DietaryType
- Classification models for recipes

### Nutrition
- Nutrition information for recipes and ingredients

### Bookmark, RecipeHistory
- User interaction tracking

### RecipeShare
- Recipe sharing with unique share IDs

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Admin Panel
Visit `http://127.0.0.1:8000/admin/` and login with superuser credentials.

## Notes

- All endpoints that require authentication use JWT tokens
- Include `Authorization: Bearer <access_token>` header for authenticated requests
- Pagination is enabled for list endpoints (default: 20 items per page)
- Media files (images) are served at `/media/` in development
- CORS is configured to allow requests from `http://localhost:3000`
