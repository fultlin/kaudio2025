"""
URL configuration for kaudio_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
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

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/', include('kaudio.urls')),
    
    path('api/upload/profile-image/', ProfileImageUploadView.as_view(), name='upload-profile-image'),
    path('api/upload/artist-image/', ArtistImageUploadView.as_view(), name='upload-artist-image'),
    path('api/upload/album-image/', AlbumImageUploadView.as_view(), name='upload-album-image'),
    path('api/upload/track/', TrackUploadView.as_view(), name='upload-track'),    
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', 
            schema_view.without_ui(cache_timeout=0), 
            name='schema-json'),
    path('swagger/', 
         schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', 
         schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
