from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

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
router.register(r'statistics', views.StatisticsViewSet, basename='statistics')
router.register(r'track-reviews', views.TrackReviewViewSet, basename='track-review')
router.register(r'album-reviews', views.AlbumReviewViewSet, basename='album-review')

urlpatterns = [
    path('', include(router.urls)),
    
    path('api-auth/', include('rest_framework.urls')),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/login/', views.login_view, name='api_login'),
    path('auth/register/', views.register_view, name='api_register'),
    
    path('recent/tracks/', views.recent_tracks, name='recent_tracks'),
    path('recent/albums/', views.recent_albums, name='recent_albums'),
]
