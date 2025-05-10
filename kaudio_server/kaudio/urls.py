from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

# Настройка маршрутов для REST API
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'artists', views.ArtistViewSet)
router.register(r'genres', views.GenreViewSet)
router.register(r'albums', views.AlbumViewSet)
router.register(r'tracks', views.TrackViewSet)
router.register(r'playlists', views.PlaylistViewSet)
router.register(r'user-activities', views.UserActivityViewSet)
router.register(r'subscribes', views.SubscribeViewSet)
router.register(r'user-subscribes', views.UserSubscribeViewSet)
router.register(r'user-albums', views.UserAlbumViewSet)
router.register(r'user-tracks', views.UserTrackViewSet)
router.register(r'playlist-tracks', views.PlaylistTrackViewSet)
router.register(r'album-genres', views.AlbumGenreViewSet)
router.register(r'track-genres', views.TrackGenreViewSet)

# Основные URL маршруты приложения kaudio
urlpatterns = [
    # Включаем автоматически созданные API маршруты
    path('', include(router.urls)),
    
    # Аутентификация
    path('api-auth/', include('rest_framework.urls')),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/register/', views.register_view, name='api_register'),
]

# ВАЖНО: Эндпоинты для загрузки файлов определены в корневом urls.py 