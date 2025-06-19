from rest_framework import serializers
from rest_framework.request import Request
from .models import (
    User, Artist, Genre, Album, Track, Playlist, UserActivity, 
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre, Statistics, TrackReview, AlbumReview
)
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, Optional, List, Union
from django.db.models import Model


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.
    
    Предоставляет полную информацию о пользователе включая изображение профиля.
    """
    profile_image_url = serializers.SerializerMethodField()
    img_profile_url = serializers.SerializerMethodField()  # для обратной совместимости
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_image', 'profile_image_url', 'img_profile_url', 'role', 'last_login', 'date_joined']
        read_only_fields = ['last_login', 'date_joined']

    def get_profile_image_url(self, obj: User) -> Optional[str]:
        """
        Получает полный URL изображения профиля пользователя.
        
        Args:
            obj: Объект пользователя
            
        Returns:
            Optional[str]: Полный URL изображения или None
        """
        if not obj.profile_image:
            return None
        try:
            request: Request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        except Exception as e:
            print(f"Ошибка при получении URL изображения профиля: {str(e)}")
            return None

    def get_img_profile_url(self, obj: User) -> Optional[str]:
        """
        Получает URL изображения профиля для обратной совместимости.
        
        Args:
            obj: Объект пользователя
            
        Returns:
            Optional[str]: URL изображения профиля или None
        """
        if obj.profile_image:
            return self.context['request'].build_absolute_uri(obj.profile_image.url)
        return None


class ArtistSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Artist.
    
    Предоставляет информацию об исполнителе включая изображение обложки.
    """
    cover_image_url = serializers.SerializerMethodField()
    img_cover_url = serializers.SerializerMethodField()  # для обратной совместимости
    user = UserSerializer(read_only=True)
    username = serializers.CharField(read_only=True)
    
    class Meta:
        model = Artist
        fields = ['id', 'bio', 'email', 'cover_image', 'cover_image_url', 'img_cover_url', 'is_verified', 'monthly_listeners', 'user', 'username']
        read_only_fields = ['monthly_listeners', 'username']

    def get_cover_image_url(self, obj: Artist) -> Optional[str]:
        """
        Получает полный URL изображения обложки исполнителя.
        
        Args:
            obj: Объект исполнителя
            
        Returns:
            Optional[str]: Полный URL изображения или None
        """
        if obj.cover_image:
            return self.context['request'].build_absolute_uri(obj.cover_image.url)
        return None

    def get_img_cover_url(self, obj: Artist) -> Optional[str]:
        """
        Получает URL изображения обложки для обратной совместимости.
        
        Args:
            obj: Объект исполнителя
            
        Returns:
            Optional[str]: URL изображения обложки или None
        """
        if obj.cover_image:
            return self.context['request'].build_absolute_uri(obj.cover_image.url)
        return None


class GenreSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Genre.
    
    Предоставляет информацию о музыкальном жанре.
    """
    class Meta:
        model = Genre
        fields = ['id', 'title', 'img_url']


class AlbumSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Album.
    
    Предоставляет полную информацию об альбоме включая исполнителя и жанры.
    """
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
    """
    Сериализатор для модели Track.
    
    Предоставляет полную информацию о треке включая исполнителя, альбом и жанры.
    """
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
    calculated_avg_rating = serializers.FloatField(read_only=True)
    total_plays = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'artist_id', 'album', 'album_id',
            'audio_file', 'track_number', 'release_date', 'cover_image',
            'duration', 'play_count', 'likes_count', 'is_explicit',
            'lyrics', 'genres', 'calculated_avg_rating', 'total_plays', 'avg_rating'
        ]
        read_only_fields = ['play_count', 'likes_count', 'calculated_avg_rating', 'total_plays', 'avg_rating']
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация данных трека.
        
        Проверяет уникальность названия трека в альбоме.
        
        Args:
            data: Данные для валидации
            
        Returns:
            Dict[str, Any]: Валидированные данные
            
        Raises:
            serializers.ValidationError: Если название трека не уникально в альбоме
        """
        title = data.get('title')
        album = data.get('album')
        
        if album and title:
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
    """
    Сериализатор для модели Playlist.
    
    Предоставляет полную информацию о плейлисте включая пользователя и треки.
    """
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

    def update(self, instance: Playlist, validated_data: Dict[str, Any]) -> Playlist:
        """
        Обновляет плейлист.
        
        Если пользователь не указан, использует существующего.
        
        Args:
            instance: Экземпляр плейлиста для обновления
            validated_data: Валидированные данные
            
        Returns:
            Playlist: Обновленный плейлист
        """
        if 'user' not in validated_data:
            validated_data['user'] = instance.user
        return super().update(instance, validated_data)


class PlaylistTrackSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели PlaylistTrack.
    
    Предоставляет информацию о связи трека с плейлистом.
    """
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
    """
    Сериализатор для модели UserActivity.
    
    Предоставляет полную информацию об активности пользователя.
    """
    user = UserSerializer(read_only=True)
    track = TrackSerializer(read_only=True)
    album = AlbumSerializer(read_only=True)
    playlist = PlaylistSerializer(read_only=True)
    artist = ArtistSerializer(read_only=True)
    
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
    
    def get_activity_type_display(self, obj: UserActivity) -> str:
        """
        Возвращает человекочитаемое название типа активности.
        
        Args:
            obj: Объект активности
            
        Returns:
            str: Человекочитаемое название типа активности
        """
        activity_types = {
            'play': 'Прослушивание',
            'like': 'Лайк',
            'like_album': 'Лайк альбома',
            'add_to_playlist': 'Добавление в плейлист',
            'remove_from_playlist': 'Удаление из плейлиста',
            'follow_artist': 'Подписка на исполнителя',
        }
        return activity_types.get(obj.activity_type, obj.activity_type)
    
    def get_formatted_timestamp(self, obj: UserActivity) -> str:
        """
        Возвращает отформатированную дату активности.
        
        Args:
            obj: Объект активности
            
        Returns:
            str: Отформатированная дата
        """
        return obj.timestamp.strftime('%d.%m.%Y %H:%M')


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Subscribe.
    
    Предоставляет информацию о типе подписки.
    """
    class Meta:
        model = Subscribe
        fields = ['id', 'type', 'permissions']


class UserSubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели UserSubscribe.
    
    Предоставляет информацию о подписке пользователя.
    """
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
    """
    Сериализатор для модели UserAlbum.
    
    Предоставляет информацию об альбоме в библиотеке пользователя.
    """
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
    """
    Сериализатор для модели UserTrack.
    
    Предоставляет информацию о треке в библиотеке пользователя.
    """
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
    """
    Сериализатор для модели AlbumGenre.
    
    Предоставляет информацию о связи альбома с жанром.
    """
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
    """
    Сериализатор для модели TrackGenre.
    
    Предоставляет информацию о связи трека с жанром.
    """
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
    """
    Сериализатор для модели Statistics.
    
    Предоставляет URL для различных типов статистики.
    """
    genre_statistics_url = serializers.URLField(read_only=True)
    popular_tracks_url = serializers.URLField(read_only=True)
    top_artists_url = serializers.URLField(read_only=True)
    
    class Meta:
        model = Statistics
        fields = ['genre_statistics_url', 'popular_tracks_url', 'top_artists_url']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для отзывов.
    
    Предоставляет общую функциональность для отзывов на треки и альбомы.
    """
    author = serializers.SerializerMethodField()
    author_id = serializers.IntegerField(source='author.id', read_only=True)

    class Meta:
        fields = ['id', 'author', 'author_id', 'rating', 'text', 'created_at', 'updated_at']
        read_only_fields = ['author', 'author_id', 'created_at', 'updated_at']

    def get_author(self, obj: Union[TrackReview, AlbumReview]) -> Dict[str, Any]:
        """
        Получает информацию об авторе отзыва.
        
        Args:
            obj: Объект отзыва
            
        Returns:
            Dict[str, Any]: Информация об авторе
        """
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'email': obj.author.email
        }


class TrackReviewSerializer(ReviewSerializer):
    """
    Сериализатор для модели TrackReview.
    
    Предоставляет информацию об отзыве на трек.
    """
    track = serializers.PrimaryKeyRelatedField(queryset=Track.objects.all())

    class Meta(ReviewSerializer.Meta):
        model = TrackReview
        fields = ReviewSerializer.Meta.fields + ['track']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация отзыва на трек.
        
        Проверяет, что пользователь не оставлял отзыв на этот трек ранее.
        
        Args:
            data: Данные для валидации
            
        Returns:
            Dict[str, Any]: Валидированные данные
            
        Raises:
            serializers.ValidationError: Если отзыв уже существует
        """
        user = self.context['request'].user
        track = data.get('track')
        
        if TrackReview.objects.filter(author=user, track=track).exists():
            raise serializers.ValidationError(
                'Вы уже оставляли отзыв на этот трек'
            )
        
        return data


class AlbumReviewSerializer(ReviewSerializer):
    """
    Сериализатор для модели AlbumReview.
    
    Предоставляет информацию об отзыве на альбом.
    """
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all())

    class Meta(ReviewSerializer.Meta):
        model = AlbumReview
        fields = ReviewSerializer.Meta.fields + ['album']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация отзыва на альбом.
        Проверяет, что пользователь не оставлял отзыв на этот альбом ранее
        и что пользователь действительно прослушивал этот альбом.
        Args:
            data: Данные для валидации
        Returns:
            Dict[str, Any]: Валидированные данные
        Raises:
            serializers.ValidationError: Если отзыв уже существует или не было прослушивания
        """
        user = self.context['request'].user
        album = data.get('album')
        if AlbumReview.objects.filter(author=user, album=album).exists():
            raise serializers.ValidationError(
                'Вы уже оставляли отзыв на этот альбом'
            )
        # Проверка на факт прослушивания
        from kaudio.models import UserActivity
        has_play = UserActivity.objects.filter(user=user, album=album, activity_type='play').exists()
        if not has_play:
            raise serializers.ValidationError(
                'Вы не можете оставить отзыв на альбом, который не прослушивали.'
            )
        return data 