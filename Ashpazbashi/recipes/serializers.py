from rest_framework import serializers
from urllib.parse import unquote
from .models import Recipe, RecipeIngredient, RecipeRating, RecipeGeneration
from ingredients.models import Ingredient
from ingredients.serializers import IngredientSerializer
from categories.models import Category, Tag, DietaryType
from categories.serializers import CategorySerializer, TagSerializer, DietaryTypeSerializer
from users.serializers import UserSerializer
from nutrition.serializers import NutritionSerializer


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        write_only=True
    )
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'ingredient_id', 'quantity', 'notes', 'order']
        read_only_fields = ['id']


class RecipeRatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = RecipeRating
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class RecipeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for recipe lists"""
    author = serializers.StringRelatedField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    dietary_types = DietaryTypeSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'prep_time', 'cook_time',
            'servings', 'difficulty', 'image', 'author', 'category',
            'tags', 'dietary_types', 'views_count', 'average_rating',
            'ratings_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'views_count', 'average_rating', 'ratings_count', 'created_at', 'updated_at']
    
    def get_image(self, obj):
        """Custom method to handle external image URLs"""
        if not obj.image:
            return None
        
        # Get the image name/path from the model field
        # If it's stored as a string in the database, use the name attribute
        image_name = obj.image.name if hasattr(obj.image, 'name') else str(obj.image)
        
        # Check if the path contains URL-encoded external URL (http%3A or https%3A)
        if 'http%3A' in image_name or 'https%3A' in image_name:
            # First decode the URL-encoded string
            decoded_url = unquote(image_name)
            # Now decoded_url might be: "https://blog.okcs.com/wp-content/uploads/2021/05/1-1-2.jpg"
            # or "http://127.0.0.1:8000/media/https://blog.okcs.com/..."
            # Extract the part after /media/ if present
            if '/media/' in decoded_url:
                url_part = decoded_url.split('/media/')[-1]
                # If the extracted part is a full external URL, use it directly
                if url_part.startswith('http://') or url_part.startswith('https://'):
                    return url_part
                else:
                    # If not, use the decoded URL as is
                    return decoded_url
            else:
                # If it's already a full external URL, return it
                if decoded_url.startswith('http://') or decoded_url.startswith('https://'):
                    return decoded_url
                # Otherwise, it might be a relative path
                return decoded_url
        # Check if it's already a full external URL (not from localhost)
        elif image_name.startswith('https://'):
            return image_name
        elif image_name.startswith('http://') and '127.0.0.1' not in image_name and 'localhost' not in image_name:
            return image_name
        # Otherwise, it's a local file - return the full URL
        else:
            request = self.context.get('request')
            if request and hasattr(obj.image, 'url'):
                return request.build_absolute_uri(obj.image.url)
            elif hasattr(obj.image, 'url'):
                return obj.image.url
            else:
                return str(obj.image)


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for recipe detail view"""
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    dietary_types = DietaryTypeSerializer(many=True, read_only=True)
    recipe_ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    nutrition = NutritionSerializer(read_only=True)
    ratings = RecipeRatingSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    
    # For write operations
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        required=False
    )
    dietary_type_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=DietaryType.objects.all(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'description', 'instructions', 'prep_time', 'cook_time',
            'servings', 'difficulty', 'image', 'author', 'category', 'category_id',
            'tags', 'tag_ids', 'dietary_types', 'dietary_type_ids',
            'recipe_ingredients', 'nutrition', 'ratings',
            'views_count', 'average_rating', 'ratings_count', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'views_count', 'average_rating', 'ratings_count',
            'created_at', 'updated_at'
        ]
    
    def get_image(self, obj):
        """Custom method to handle external image URLs"""
        if not obj.image:
            return None
        
        # Get the image name/path from the model field
        # If it's stored as a string in the database, use the name attribute
        image_name = obj.image.name if hasattr(obj.image, 'name') else str(obj.image)
        
        # Check if the path contains URL-encoded external URL (http%3A or https%3A)
        if 'http%3A' in image_name or 'https%3A' in image_name:
            # First decode the URL-encoded string
            decoded_url = unquote(image_name)
            # Now decoded_url might be: "https://blog.okcs.com/wp-content/uploads/2021/05/1-1-2.jpg"
            # or "http://127.0.0.1:8000/media/https://blog.okcs.com/..."
            # Extract the part after /media/ if present
            if '/media/' in decoded_url:
                url_part = decoded_url.split('/media/')[-1]
                # If the extracted part is a full external URL, use it directly
                if url_part.startswith('http://') or url_part.startswith('https://'):
                    return url_part
                else:
                    # If not, use the decoded URL as is
                    return decoded_url
            else:
                # If it's already a full external URL, return it
                if decoded_url.startswith('http://') or decoded_url.startswith('https://'):
                    return decoded_url
                # Otherwise, it might be a relative path
                return decoded_url
        # Check if it's already a full external URL (not from localhost)
        elif image_name.startswith('https://'):
            return image_name
        elif image_name.startswith('http://') and '127.0.0.1' not in image_name and 'localhost' not in image_name:
            return image_name
        # Otherwise, it's a local file - return the full URL
        else:
            request = self.context.get('request')
            if request and hasattr(obj.image, 'url'):
                return request.build_absolute_uri(obj.image.url)
            elif hasattr(obj.image, 'url'):
                return obj.image.url
            else:
                return str(obj.image)
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        dietary_type_ids = validated_data.pop('dietary_type_ids', [])
        category_id = validated_data.pop('category_id', None)
        
        recipe = Recipe.objects.create(**validated_data)
        
        if tag_ids:
            recipe.tags.set(tag_ids)
        if dietary_type_ids:
            recipe.dietary_types.set(dietary_type_ids)
        
        return recipe
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        dietary_type_ids = validated_data.pop('dietary_type_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        if dietary_type_ids is not None:
            instance.dietary_types.set(dietary_type_ids)
        
        return instance


class RecipeGenerationSerializer(serializers.ModelSerializer):
    recipe = RecipeListSerializer(read_only=True)
    
    class Meta:
        model = RecipeGeneration
        fields = [
            'id', 'user', 'prompt', 'status', 'recipe',
            'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'recipe', 'error_message', 'created_at', 'updated_at']


