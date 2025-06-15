from rest_framework import serializers
from .models import (
    User, Artist, Genre, Album, Track, Playlist, UserActivity, 
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre, Statistics, TrackReview, AlbumReview
)
from django.utils.translation import gettext_lazy as _


class UserSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    img_profile_url = serializers.SerializerMethodField()  # для обратной совместимости
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_image', 'profile_image_url', 'img_profile_url', 'role', 'last_login', 'date_joined']
        read_only_fields = ['last_login', 'date_joined']

    def get_profile_image_url(self, obj):
        if not obj.profile_image:
            return None
        try:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        except Exception as e:
            print(f"Ошибка при получении URL изображения профиля: {str(e)}")
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
    username = serializers.CharField(read_only=True)
    
    class Meta:
        model = Artist
        fields = ['id', 'bio', 'email', 'cover_image', 'cover_image_url', 'img_cover_url', 'is_verified', 'monthly_listeners', 'user', 'username']
        read_only_fields = ['monthly_listeners', 'username']

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
        write_only=True,
        required=False,
        allow_null=True
    )
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'artist_id', 'album', 'album_id',
            'audio_file', 'track_number', 'release_date', 'cover_image',
            'duration', 'play_count', 'likes_count', 'is_explicit',
            'lyrics', 'genres'
        ]
        read_only_fields = ['play_count', 'likes_count']
    
    def validate(self, data):
        """Проверяет уникальность названия трека в альбоме"""
        title = data.get('title')
        album = data.get('album')
        
        if album and title:
            # Проверяем, существует ли трек с таким же названием в альбоме
            existing_track = Track.objects.filter(
                album=album,
                title__iexact=title
            ).exclude(pk=self.instance.pk if self.instance else None).first()
            
            if existing_track:
                raise serializers.ValidationError({
                    'title': _('Трек с таким названием уже существует в этом альбоме')
                })
        
        return data


class PlaylistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False
    )
    tracks = TrackSerializer(many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'title', 'user', 'user_id', 'cover_image', 'creation_date',
            'is_public', 'total_tracks', 'total_duration', 'tracks'
        ]
        read_only_fields = ['creation_date', 'total_tracks', 'total_duration']

    def update(self, instance, validated_data):
        if 'user' not in validated_data:
            validated_data['user'] = instance.user
        return super().update(instance, validated_data)


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
    track = TrackSerializer(read_only=True)
    album = AlbumSerializer(read_only=True)
    playlist = PlaylistSerializer(read_only=True)
    artist = ArtistSerializer(read_only=True)
    
    # Дополнительные поля для удобства
    activity_type_display = serializers.SerializerMethodField()
    formatted_timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'track', 'album', 'playlist', 'artist',
            'duration', 'timestamp', 'formatted_timestamp'
        ]
        read_only_fields = ['timestamp']
    
    def get_activity_type_display(self, obj):
        """Возвращает человекочитаемое название типа активности"""
        activity_types = {
            'play': 'Прослушивание',
            'like': 'Лайк',
            'like_album': 'Лайк альбома',
            'follow_artist': 'Подписка на исполнителя',
            'add_to_playlist': 'Добавление в плейлист',
            'remove_from_playlist': 'Удаление из плейлиста'
        }
        return activity_types.get(obj.activity_type, obj.activity_type)
    
    def get_formatted_timestamp(self, obj):
        """Возвращает отформатированную дату и время"""
        from django.utils import timezone
        
        if not obj.timestamp:
            return None
            
        # Если timestamp в UTC, конвертируем в локальное время
        if timezone.is_aware(obj.timestamp):
            local_time = timezone.localtime(obj.timestamp)
        else:
            local_time = obj.timestamp
            
        return local_time.strftime('%d.%m.%Y %H:%M')


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


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    author_id = serializers.IntegerField(source='author.id', read_only=True)

    class Meta:
        fields = ['id', 'author', 'author_id', 'rating', 'text', 'created_at', 'updated_at']
        read_only_fields = ['author', 'author_id', 'created_at', 'updated_at']

    def get_author(self, obj):
        return obj.author.username


class TrackReviewSerializer(ReviewSerializer):
    track = serializers.PrimaryKeyRelatedField(queryset=Track.objects.all())
    
    class Meta(ReviewSerializer.Meta):
        model = TrackReview
        fields = ReviewSerializer.Meta.fields + ['track']

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        track = data.get('track') or getattr(self.instance, 'track', None)
        if user and track:
            from kaudio.models import UserActivity
            has_play = UserActivity.objects.filter(user=user, track=track, activity_type='play').exists()
            if not has_play:
                raise serializers.ValidationError('Вы не можете оставить отзыв на трек, который не прослушивали.')
        return super().validate(data)


class AlbumReviewSerializer(ReviewSerializer):
    class Meta(ReviewSerializer.Meta):
        model = AlbumReview
        fields = ReviewSerializer.Meta.fields + ['album']

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        album = data.get('album') or getattr(self.instance, 'album', None)
        if user and album:
            from kaudio.models import UserActivity
            has_play = UserActivity.objects.filter(user=user, album=album, activity_type='play').exists()
            if not has_play:
                raise serializers.ValidationError('Вы не можете оставить отзыв на альбом, который не прослушивали.')
        return super().validate(data) 