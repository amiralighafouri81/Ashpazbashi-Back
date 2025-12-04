"""
URL configuration for Ashpazbashi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('playground/', include('playground.urls')),
    # All API endpoints under /api/
    # Each app's router registers its own resource name (e.g., 'recipes', 'ingredients')
    path('api/auth/', include('users.urls')),  # /api/auth/users/, /api/auth/jwt/create/
    path('api/', include('recipes.urls')),      # /api/recipes/
    path('api/', include('ingredients.urls')),  # /api/ingredients/
    path('api/', include('nutrition.urls')),    # /api/nutrition/
    path('api/', include('bookmarks.urls')),    # /api/bookmarks/
    path('api/', include('history.urls')),      # /api/history/
    path('api/', include('categories.urls')),   # /api/categories/, /api/tags/, /api/dietary-types/
    path('api/', include('sharing.urls')),      # /api/share/
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
