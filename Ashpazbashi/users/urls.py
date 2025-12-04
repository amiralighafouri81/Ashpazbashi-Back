from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView, UserProfileView, CustomTokenObtainPairView,
    user_profile_detail, dietary_preferences
)

urlpatterns = [
    # Auth endpoints
    path('users/', UserRegistrationView.as_view(), name='user-registration'),
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    # User profile endpoints
    path('profile/', user_profile_detail, name='user-profile-detail'),
    path('dietary-preferences/', dietary_preferences, name='dietary-preferences'),
]

