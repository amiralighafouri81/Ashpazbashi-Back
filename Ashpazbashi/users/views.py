from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserRegistrationSerializer, UserProfileSerializer
from .models import UserProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """POST /auth/users/ - User registration"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /auth/users/me/ - Get/Update current user profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_detail(request):
    """GET/PUT /api/users/profile - Get/Update user profile with dietary preferences"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def dietary_preferences(request):
    """GET/PUT /api/users/dietary-preferences - Get/Update dietary preferences"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        return Response({
            'dietary_preferences': profile.dietary_preferences,
            'favorite_cuisines': profile.favorite_cuisines,
            'cooking_skill_level': profile.cooking_skill_level,
        })
    
    elif request.method == 'PUT':
        data = request.data
        if 'dietary_preferences' in data:
            profile.dietary_preferences = data['dietary_preferences']
        if 'favorite_cuisines' in data:
            profile.favorite_cuisines = data['favorite_cuisines']
        if 'cooking_skill_level' in data:
            profile.cooking_skill_level = data['cooking_skill_level']
        profile.save()
        return Response({
            'dietary_preferences': profile.dietary_preferences,
            'favorite_cuisines': profile.favorite_cuisines,
            'cooking_skill_level': profile.cooking_skill_level,
        })
