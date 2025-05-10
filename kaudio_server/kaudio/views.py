from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import (
    User, Artist, Genre, Album, Track, Playlist, UserActivity,
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre
)
from .serializers import (
    UserSerializer, ArtistSerializer, GenreSerializer, AlbumSerializer,
    TrackSerializer, PlaylistSerializer, UserActivitySerializer,
    SubscribeSerializer, UserSubscribeSerializer, UserAlbumSerializer,
    UserTrackSerializer, PlaylistTrackSerializer, AlbumGenreSerializer,
    TrackGenreSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'date_joined']

    @action(detail=True, methods=['get'])
    def playlists(self, request, pk=None):
        user = self.get_object()
        playlists = Playlist.objects.filter(user=user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user)
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def subscribes(self, request, pk=None):
        user = self.get_object()
        subscribes = UserSubscribe.objects.filter(user=user)
        serializer = UserSubscribeSerializer(subscribes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        user = self.get_object()
        user_albums = UserAlbum.objects.filter(user=user)
        serializer = UserAlbumSerializer(user_albums, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        user = self.get_object()
        user_tracks = UserTrack.objects.filter(user=user)
        serializer = UserTrackSerializer(user_tracks, many=True)
        return Response(serializer.data)


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email']
    ordering_fields = ['monthly_listeners']

    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        artist = self.get_object()
        albums = Album.objects.filter(artist=artist)
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        artist = self.get_object()
        tracks = Track.objects.filter(artist=artist)
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title']

    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        genre = self.get_object()
        albums = Album.objects.filter(genres=genre)
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        genre = self.get_object()
        tracks = Track.objects.filter(genres=genre)
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'artist__email']
    ordering_fields = ['release_date', 'total_tracks', 'total_duration']

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        album = self.get_object()
        tracks = Track.objects.filter(album=album)
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def genres(self, request, pk=None):
        album = self.get_object()
        genres = Genre.objects.filter(albums=album)
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'artist__email', 'album__title']
    ordering_fields = ['release_date', 'play_count', 'likes_count', 'duration']

    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        track = self.get_object()
        track.play_count += 1
        track.save()

        # Create activity if user provided
        if 'user_id' in request.data:
            try:
                user = User.objects.get(pk=request.data['user_id'])
                activity = UserActivity.objects.create(
                    user=user,
                    activity_type='play',
                    track=track,
                    duration=request.data.get('duration', track.duration)
                )
                activity_serializer = UserActivitySerializer(activity)
                return Response({
                    'track': self.get_serializer(track).data,
                    'activity': activity_serializer.data
                })
            except User.DoesNotExist:
                pass
        
        return Response(self.get_serializer(track).data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        track = self.get_object()
        track.likes_count += 1
        track.save()

        # Create activity if user provided
        if 'user_id' in request.data:
            try:
                user = User.objects.get(pk=request.data['user_id'])
                activity = UserActivity.objects.create(
                    user=user,
                    activity_type='like',
                    track=track
                )
                activity_serializer = UserActivitySerializer(activity)
                return Response({
                    'track': self.get_serializer(track).data,
                    'activity': activity_serializer.data
                })
            except User.DoesNotExist:
                pass
        
        return Response(self.get_serializer(track).data)
    
    @action(detail=True, methods=['get'])
    def genres(self, request, pk=None):
        track = self.get_object()
        genres = Genre.objects.filter(tracks=track)
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'user__username']
    ordering_fields = ['creation_date', 'total_tracks', 'total_duration']

    def get_queryset(self):
        queryset = Playlist.objects.all()
        
        # Filter out private playlists unless they belong to the requesting user
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(
                Q(is_public=True) | Q(user__id=user_id)
            )
        else:
            queryset = queryset.filter(is_public=True)
        
        return queryset

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        playlist = self.get_object()
        playlist_tracks = PlaylistTrack.objects.filter(playlist=playlist).order_by('position')
        serializer = PlaylistTrackSerializer(playlist_tracks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_track(self, request, pk=None):
        playlist = self.get_object()
        
        if 'track_id' not in request.data:
            return Response({'error': 'track_id is required'}, status=400)
        
        try:
            track = Track.objects.get(pk=request.data['track_id'])
        except Track.DoesNotExist:
            return Response({'error': 'Track not found'}, status=404)
        
        # Get the highest position or default to 0
        max_position = PlaylistTrack.objects.filter(playlist=playlist).order_by('-position').first()
        position = (max_position.position + 1) if max_position else 1
        
        # Create the association
        playlist_track = PlaylistTrack.objects.create(
            playlist=playlist,
            track=track,
            position=position
        )
        
        # Update playlist statistics
        playlist.total_tracks = PlaylistTrack.objects.filter(playlist=playlist).count()
        playlist.total_duration += track.duration
        playlist.save()
        
        # Create activity if user provided
        if 'user_id' in request.data:
            try:
                user = User.objects.get(pk=request.data['user_id'])
                activity = UserActivity.objects.create(
                    user=user,
                    activity_type='add_to_playlist',
                    track=track,
                    playlist=playlist
                )
            except User.DoesNotExist:
                pass
        
        return Response(PlaylistTrackSerializer(playlist_track).data)

    @action(detail=True, methods=['post'])
    def remove_track(self, request, pk=None):
        playlist = self.get_object()
        
        if 'track_id' not in request.data:
            return Response({'error': 'track_id is required'}, status=400)
        
        try:
            track = Track.objects.get(pk=request.data['track_id'])
            playlist_track = PlaylistTrack.objects.get(playlist=playlist, track=track)
        except (Track.DoesNotExist, PlaylistTrack.DoesNotExist):
            return Response({'error': 'Track not found in playlist'}, status=404)
        
        # Update playlist statistics
        playlist.total_tracks -= 1
        playlist.total_duration -= track.duration
        playlist.save()
        
        # Remove the association
        playlist_track.delete()
        
        # Reorder positions
        position = 1
        for pt in PlaylistTrack.objects.filter(playlist=playlist).order_by('position'):
            pt.position = position
            pt.save()
            position += 1
        
        return Response({'status': 'track removed from playlist'})


class UserActivityViewSet(viewsets.ModelViewSet):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'activity_type']
    ordering_fields = ['timestamp']

    def get_queryset(self):
        queryset = UserActivity.objects.all()
        
        # Filter by user_id if provided
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        
        # Filter by activity_type if provided
        activity_type = self.request.query_params.get('activity_type', None)
        if activity_type is not None:
            queryset = queryset.filter(activity_type=activity_type)
        
        return queryset


class SubscribeViewSet(viewsets.ModelViewSet):
    queryset = Subscribe.objects.all()
    serializer_class = SubscribeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['type']


class UserSubscribeViewSet(viewsets.ModelViewSet):
    queryset = UserSubscribe.objects.all()
    serializer_class = UserSubscribeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'subscribe__type']
    ordering_fields = ['start_date', 'end_date']

    def get_queryset(self):
        queryset = UserSubscribe.objects.all()
        
        # Filter by user_id if provided
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        
        return queryset


class UserAlbumViewSet(viewsets.ModelViewSet):
    queryset = UserAlbum.objects.all()
    serializer_class = UserAlbumSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'album__title']
    ordering_fields = ['position', 'added_at']

    def get_queryset(self):
        queryset = UserAlbum.objects.all()
        
        # Filter by user_id if provided
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        
        return queryset


class UserTrackViewSet(viewsets.ModelViewSet):
    queryset = UserTrack.objects.all()
    serializer_class = UserTrackSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'track__title']
    ordering_fields = ['position', 'added_at']

    def get_queryset(self):
        queryset = UserTrack.objects.all()
        
        # Filter by user_id if provided
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        
        return queryset


class PlaylistTrackViewSet(viewsets.ModelViewSet):
    queryset = PlaylistTrack.objects.all()
    serializer_class = PlaylistTrackSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['playlist__title', 'track__title']
    ordering_fields = ['position', 'added_at']

    def get_queryset(self):
        queryset = PlaylistTrack.objects.all()
        
        # Filter by playlist_id if provided
        playlist_id = self.request.query_params.get('playlist_id', None)
        if playlist_id is not None:
            queryset = queryset.filter(playlist__id=playlist_id)
        
        return queryset


class AlbumGenreViewSet(viewsets.ModelViewSet):
    queryset = AlbumGenre.objects.all()
    serializer_class = AlbumGenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['album__title', 'genre__title']

    def get_queryset(self):
        queryset = AlbumGenre.objects.all()
        
        # Filter by album_id if provided
        album_id = self.request.query_params.get('album_id', None)
        if album_id is not None:
            queryset = queryset.filter(album__id=album_id)
        
        # Filter by genre_id if provided
        genre_id = self.request.query_params.get('genre_id', None)
        if genre_id is not None:
            queryset = queryset.filter(genre__id=genre_id)
        
        return queryset


class TrackGenreViewSet(viewsets.ModelViewSet):
    queryset = TrackGenre.objects.all()
    serializer_class = TrackGenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['track__title', 'genre__title']

    def get_queryset(self):
        queryset = TrackGenre.objects.all()
        
        # Filter by track_id if provided
        track_id = self.request.query_params.get('track_id', None)
        if track_id is not None:
            queryset = queryset.filter(track__id=track_id)
        
        # Filter by genre_id if provided
        genre_id = self.request.query_params.get('genre_id', None)
        if genre_id is not None:
            queryset = queryset.filter(genre__id=genre_id)
        
        return queryset 