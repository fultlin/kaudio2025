"""
URL конфигурация для приложения kaudio.

Определяет маршруты для всех API эндпоинтов включая:
- CRUD операции для всех моделей
- Аутентификация и регистрация
- Загрузка файлов
- Статистика и аналитика
- Оптимизированные эндпоинты
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserViewSet, ArtistViewSet, GenreViewSet, AlbumViewSet, TrackViewSet,
    PlaylistViewSet, UserActivityViewSet, SubscribeViewSet, UserSubscribeViewSet,
    UserAlbumViewSet, UserTrackViewSet, PlaylistTrackViewSet, AlbumGenreViewSet,
    TrackGenreViewSet, StatisticsViewSet, TrackReviewViewSet, AlbumReviewViewSet,
    OptimizedTrackListView, OptimizedPlaylistListView, OptimizedUserReviewsView,
    login_view, register_view, upload_track_view, recent_tracks, recent_albums,
    get_tracks_analytics, get_user_activity
)

# Роутер для ViewSet'ов
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'artists', ArtistViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'user-activities', UserActivityViewSet)
router.register(r'subscribes', SubscribeViewSet)
router.register(r'user-subscribes', UserSubscribeViewSet)
router.register(r'user-albums', UserAlbumViewSet)
router.register(r'user-tracks', UserTrackViewSet)
router.register(r'playlist-tracks', PlaylistTrackViewSet)
router.register(r'album-genres', AlbumGenreViewSet)
router.register(r'track-genres', TrackGenreViewSet)
router.register(r'statistics', StatisticsViewSet, basename='statistics')
router.register(r'track-reviews', TrackReviewViewSet, basename='track-review')
router.register(r'album-reviews', AlbumReviewViewSet, basename='album-review')

urlpatterns = [
    # Основные API маршруты через роутер
    path('', include(router.urls)),
    
    # Аутентификация и авторизация
    path('api-auth/', include('rest_framework.urls')),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
    
    # Загрузка и управление контентом
    path('upload-track/', upload_track_view, name='upload-track'),
    
    # Недавний контент
    path('recent/tracks/', recent_tracks, name='recent-tracks'),
    path('recent/albums/', recent_albums, name='recent-albums'),
    
    # Аналитика и статистика
    path('tracks-analytics/', get_tracks_analytics, name='tracks-analytics'),
    path('user-activity/', get_user_activity, name='user-activity'),
    
    # Оптимизированные эндпоинты для улучшенной производительности
    path('optimized/tracks/', OptimizedTrackListView.as_view(), name='optimized-tracks'),
    path('optimized/playlists/', OptimizedPlaylistListView.as_view(), name='optimized-playlists'),
    path('optimized/reviews/', OptimizedUserReviewsView.as_view(), name='optimized-reviews'),
]
