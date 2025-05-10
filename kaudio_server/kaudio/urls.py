from django.urls import path, include
from rest_framework.routers import DefaultRouter
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

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] 