from rest_framework import serializers
from .models import (
    User, Artist, Genre, Album, Track, Playlist, UserActivity, 
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre, Statistics
)


class UserSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    img_profile_url = serializers.SerializerMethodField()  # для обратной совместимости
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_image', 'profile_image_url', 'img_profile_url', 'role', 'last_login', 'date_joined']
        read_only_fields = ['last_login', 'date_joined']

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return self.context['request'].build_absolute_uri(obj.profile_image.url)
        return None

    def get_img_profile_url(self, obj):
        # Для обратной совместимости возвращаем то же значение
        if obj.profile_image:
            return self.context['request'].build_absolute_uri(obj.profile_image.url)
        return None


class ArtistSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    img_cover_url = serializers.SerializerMethodField()  # для обратной совместимости
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Artist
        fields = ['id', 'bio', 'email', 'cover_image', 'cover_image_url', 'img_cover_url', 'is_verified', 'monthly_listeners', 'user']
        read_only_fields = ['monthly_listeners']

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return self.context['request'].build_absolute_uri(obj.cover_image.url)
        return None

    def get_img_cover_url(self, obj):
        # Для обратной совместимости
        if obj.cover_image:
            return self.context['request'].build_absolute_uri(obj.cover_image.url)
        return None


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'title', 'img_url']


class AlbumSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(),
        source='artist',
        write_only=True
    )
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Album
        fields = [
            'id', 'title', 'artist', 'artist_id', 'release_date', 
            'cover_image', 'total_tracks', 'total_duration', 'genres'
        ]
        read_only_fields = ['total_tracks', 'total_duration']


class TrackSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(),
        source='artist',
        write_only=True
    )
    album = AlbumSerializer(read_only=True)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(),
        source='album',
        write_only=True
    )
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'artist_id', 'album', 'album_id',
            'track_number', 'release_date', 'cover_image', 'duration', 
            'play_count', 'likes_count', 'is_explicit', 'lyrics', 'genres'
        ]
        read_only_fields = ['play_count', 'likes_count']


class PlaylistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    tracks = TrackSerializer(many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'title', 'user', 'user_id', 'cover_image', 'creation_date',
            'is_public', 'total_tracks', 'total_duration', 'tracks'
        ]
        read_only_fields = ['creation_date', 'total_tracks', 'total_duration']


class PlaylistTrackSerializer(serializers.ModelSerializer):
    playlist = PlaylistSerializer(read_only=True)
    playlist_id = serializers.PrimaryKeyRelatedField(
        queryset=Playlist.objects.all(),
        source='playlist',
        write_only=True
    )
    track = TrackSerializer(read_only=True)
    track_id = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all(),
        source='track',
        write_only=True
    )

    class Meta:
        model = PlaylistTrack
        fields = ['id', 'playlist', 'playlist_id', 'track', 'track_id', 'position', 'added_at']
        read_only_fields = ['added_at']


class UserActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    track = TrackSerializer(read_only=True)
    track_id = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all(),
        source='track',
        write_only=True,
        required=False,
        allow_null=True
    )
    album = AlbumSerializer(read_only=True)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(),
        source='album',
        write_only=True,
        required=False,
        allow_null=True
    )
    playlist = PlaylistSerializer(read_only=True)
    playlist_id = serializers.PrimaryKeyRelatedField(
        queryset=Playlist.objects.all(),
        source='playlist',
        write_only=True,
        required=False,
        allow_null=True
    )
    artist = ArtistSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(),
        source='artist',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_id', 'activity_type', 
            'track', 'track_id', 'album', 'album_id', 'playlist', 'playlist_id',
            'artist', 'artist_id', 'duration', 'timestamp'
        ]
        read_only_fields = ['timestamp']


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ['id', 'type', 'permissions']


class UserSubscribeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    subscribe = SubscribeSerializer(read_only=True)
    subscribe_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscribe.objects.all(),
        source='subscribe',
        write_only=True
    )

    class Meta:
        model = UserSubscribe
        fields = ['id', 'user', 'user_id', 'subscribe', 'subscribe_id', 'start_date', 'end_date']
        read_only_fields = ['start_date']


class UserAlbumSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    album = AlbumSerializer(read_only=True)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(),
        source='album',
        write_only=True
    )

    class Meta:
        model = UserAlbum
        fields = ['id', 'user', 'user_id', 'album', 'album_id', 'position', 'added_at']
        read_only_fields = ['added_at']


class UserTrackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    track = TrackSerializer(read_only=True)
    track_id = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all(),
        source='track',
        write_only=True
    )

    class Meta:
        model = UserTrack
        fields = ['id', 'user', 'user_id', 'track', 'track_id', 'position', 'added_at']
        read_only_fields = ['added_at']


class AlbumGenreSerializer(serializers.ModelSerializer):
    album = AlbumSerializer(read_only=True)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(),
        source='album',
        write_only=True
    )
    genre = GenreSerializer(read_only=True)
    genre_id = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        source='genre',
        write_only=True
    )

    class Meta:
        model = AlbumGenre
        fields = ['id', 'album', 'album_id', 'genre', 'genre_id']


class TrackGenreSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    track_id = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all(),
        source='track',
        write_only=True
    )
    genre = GenreSerializer(read_only=True)
    genre_id = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        source='genre',
        write_only=True
    )

    class Meta:
        model = TrackGenre
        fields = ['id', 'track', 'track_id', 'genre', 'genre_id']


class StatisticsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Statistics"""
    
    genre_statistics_url = serializers.URLField(read_only=True)
    popular_tracks_url = serializers.URLField(read_only=True)
    top_artists_url = serializers.URLField(read_only=True)
    
    class Meta:
        model = Statistics
        fields = ['genre_statistics_url', 'popular_tracks_url', 'top_artists_url'] 