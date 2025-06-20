"""
URL конфигурация для проекта kaudio_server.

Основной файл конфигурации URL для Django проекта KAudio.
Включает маршруты для:
- Административной панели Django
- API эндпоинтов приложения kaudio
- Загрузки файлов (изображения, треки)
- Swagger документации API
- Обслуживания медиа файлов

Примеры использования:
Function views:
    1. Добавить импорт: from my_app import views
    2. Добавить URL: path('', views.home, name='home')
Class-based views:
    1. Добавить импорт: from other_app.views import Home
    2. Добавить URL: path('', Home.as_view(), name='home')
Including another URLconf:
    1. Импортировать include(): from django.urls import include, path
    2. Добавить URL: path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .upload_views import ProfileImageUploadView, ArtistImageUploadView, TrackUploadView, AlbumImageUploadView
from kaudio import views as kaudio_views
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from kaudio.models import Track, Artist, Album, Genre, TrackGenre
from kaudio.serializers import TrackSerializer

# Конфигурация Swagger документации
schema_view = get_schema_view(
    openapi.Info(
        title="KAudio API",
        default_version='v1',
        description="API для музыкального сервиса KAudio",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@kaudio.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    # Административная панель Django
    path('admin/', admin.site.urls),
    
    # Sentry
    path('sentry-debug/', trigger_error),
    
    # Основные API маршруты приложения kaudio
    path('api/', include('kaudio.urls')),
    
    # API для загрузки файлов
    path('api/upload/profile-image/', ProfileImageUploadView.as_view(), name='upload-profile-image'),
    path('api/upload/artist-image/', ArtistImageUploadView.as_view(), name='upload-artist-image'),
    path('api/upload/album-image/', AlbumImageUploadView.as_view(), name='upload-album-image'),
    path('api/upload/track/', TrackUploadView.as_view(), name='upload-track'),    
    
    # Swagger документация API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    path('swagger/', 
         schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', 
         schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
    
    path('silk/', include('silk.urls', namespace='silk')),
    
    # Обслуживание медиа файлов
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/', include('allauth.socialaccount.urls')),
]

# Добавление статических файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Добавление медиа файлов
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
