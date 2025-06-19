from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.request import Request
from django.db.models import Q, Sum, Count, Avg, F, Prefetch, QuerySet
from .models import (
    Statistics, User, Artist, Genre, Album, Track, Playlist, UserActivity,
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre, TrackReview, AlbumReview
)
from .serializers import (
    StatisticsSerializer, UserSerializer, ArtistSerializer, GenreSerializer, AlbumSerializer,
    TrackSerializer, PlaylistSerializer, UserActivitySerializer,
    SubscribeSerializer, UserSubscribeSerializer, UserAlbumSerializer,
    UserTrackSerializer, PlaylistTrackSerializer, AlbumGenreSerializer,
    TrackGenreSerializer, TrackReviewSerializer, AlbumReviewSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import os
from django.conf import settings
import logging
from rest_framework.views import APIView
from django.utils import timezone
from django.http import FileResponse
from django.db.models.functions import Lower
from rest_framework.exceptions import PermissionDenied
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.db import connection
import time
from .filters import TrackFilter, AlbumFilter, ArtistFilter, PlaylistFilter, UserActivityFilter
import django_filters.rest_framework
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, cast
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

T = TypeVar('T')


def log_query_performance(func: Callable[..., T]) -> Callable[..., T]:
    """
    Декоратор для логирования производительности запросов.
    
    Логирует время выполнения и количество SQL запросов для функции.
    
    Args:
        func: Функция для обертывания
        
    Returns:
        Callable[..., T]: Обернутая функция
    """
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        queries_before = len(connection.queries)
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        queries_after = len(connection.queries)
        total_queries = queries_after - queries_before
        execution_time = end_time - start_time
        
        logger.info(f"Метод {func.__name__}:")
        logger.info(f"- Время выполнения: {execution_time:.2f} секунд")
        logger.info(f"- Количество запросов: {total_queries}")
        
        return result
    return wrapper


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями.
    
    Предоставляет CRUD операции для пользователей с различными правами доступа
    в зависимости от действия.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'date_joined']
    
    def get_permissions(self) -> List[permissions.BasePermission]:
        """
        Определяет права доступа в зависимости от действия.
        
        Returns:
            List[permissions.BasePermission]: Список классов разрешений
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обновляет пользователя.
        
        Обрабатывает пустые значения для img_profile_url.
        
        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Response: HTTP ответ
        """
        if 'img_profile_url' in request.data and request.data['img_profile_url'] == '':
            request.data['img_profile_url'] = None
        
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Частично обновляет пользователя.
        
        Обрабатывает пустые значения для img_profile_url.
        
        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Response: HTTP ответ
        """
        if 'img_profile_url' in request.data and request.data['img_profile_url'] == '':
            request.data['img_profile_url'] = None
        
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def playlists(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Получает плейлисты пользователя.
        
        Args:
            request: HTTP запрос
            pk: ID пользователя
            
        Returns:
            Response: Список плейлистов пользователя
        """
        user = self.get_object()
        playlists = Playlist.objects.filter(user=user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def activities(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Получает активности пользователя.
        
        Args:
            request: HTTP запрос
            pk: ID пользователя
            
        Returns:
            Response: Список активностей пользователя
        """
        try:
            user = self.get_object()
            
            # Проверяем, что пользователь запрашивает свои активности или является администратором
            if request.user != user and not request.user.is_staff:
                return Response(
                    {"error": "У вас нет прав для просмотра активностей этого пользователя"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Получаем активности с предзагрузкой связанных данных
            activities = UserActivity.objects.select_related(
                'track',
                'track__artist',
                'track__album',
                'album',
                'album__artist',
                'artist'
            ).filter(user=user).order_by('-timestamp')
            
            
            # Сериализуем данные с контекстом request
            serializer = UserActivitySerializer(activities, many=True, context={'request': request})
            return Response(serializer.data)
            
        except Exception as e:
            print(f"[UserActivity Error] Ошибка при получении активностей пользователя {user.username}: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Не удалось получить активности пользователя"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def subscribes(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Получает подписки пользователя.
        
        Args:
            request: HTTP запрос
            pk: ID пользователя
            
        Returns:
            Response: Список подписок пользователя
        """
        user = self.get_object()
        subscribes = UserSubscribe.objects.filter(user=user)
        serializer = UserSubscribeSerializer(subscribes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def albums(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Получает альбомы пользователя.
        
        Args:
            request: HTTP запрос
            pk: ID пользователя
            
        Returns:
            Response: Список альбомов пользователя
        """
        user = self.get_object()
        user_albums = UserAlbum.objects.filter(user=user)
        serializer = UserAlbumSerializer(user_albums, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tracks(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Получает треки пользователя.
        
        Args:
            request: HTTP запрос
            pk: ID пользователя
            
        Returns:
            Response: Список треков пользователя
        """
        user = self.get_object()
        user_tracks = UserTrack.objects.filter(user=user)
        serializer = UserTrackSerializer(user_tracks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request: Request) -> Response:
        """
        Получает информацию о текущем пользователе.
        
        Args:
            request: HTTP запрос
            
        Returns:
            Response: Информация о текущем пользователе
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ArtistViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с исполнителями.
    
    Предоставляет CRUD операции для исполнителей с фильтрацией и поиском.
    """
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ArtistFilter
    search_fields = ['email', 'bio', 'user__username']
    ordering_fields = ['monthly_listeners', 'is_verified']

    def get_queryset(self) -> QuerySet[Artist]:
        """
        Получает queryset исполнителей с фильтрацией по пользователю и поиску.
        
        Returns:
            QuerySet[Artist]: Отфильтрованный queryset исполнителей
        """
        queryset = Artist.objects.select_related('user').all()
        user_id = self.request.query_params.get('user', None)
        search = self.request.query_params.get('search', None)

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if user.email:
                    queryset = queryset.filter(email=user.email)
                else:
                    queryset = queryset.none()
            except User.DoesNotExist:
                queryset = queryset.none()

        if search:
            search = search.lower()
            queryset = queryset.annotate(
                username_lower=Lower('user__username')
            ).filter(username_lower__contains=search)

        return queryset.distinct()

    def perform_create(self, serializer: ArtistSerializer) -> None:
        """
        Создает исполнителя.
        
        Проверяем, что у пользователя еще нет профиля исполнителя.
        
        Args:
            serializer: Сериализатор с данными исполнителя
            
        Raises:
            PermissionDenied: Если у пользователя уже есть профиль исполнителя
        """
        user = self.request.user
        
        # Проверяем, есть ли уже артист с таким user_id
        existing_artist = Artist.objects.filter(user=user).first()
        if existing_artist:
            raise PermissionDenied('У вас уже есть профиль исполнителя.')
        
        serializer.save(user=user, username=user.username, email=user.email)

    def perform_update(self, serializer: ArtistSerializer) -> None:
        """
        Обновляет исполнителя.
        
        Проверяет права доступа и сохраняет неизменные поля.
        
        Args:
            serializer: Сериализатор с данными исполнителя
            
        Raises:
            PermissionDenied: Если пользователь пытается редактировать чужой профиль
        """
        instance = self.get_object()
        if instance.user != self.request.user:
            raise PermissionDenied('Вы не можете редактировать чужой профиль исполнителя.')
        # Не позволяем менять username и email артиста
        serializer.save(username=instance.user.username, email=instance.user.email)

    def list(self, request, *args, **kwargs):
        """
        Получает список исполнителей с поиском.
        
        Args:
            request: HTTP запрос
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Response: Список исполнителей
        """
        search = request.query_params.get('search', '')
        
        if not search:
            return super().list(request, *args, **kwargs)

        queryset = Artist.objects.select_related('user').all()

        exact_matches = queryset.filter(
            Q(user__username__iexact=search) |
            Q(email__iexact=search)
        )
        for artist in exact_matches:
            print(f"[Artist Search Debug] Точное совпадение: username={artist.user.username if artist.user else 'None'}, email={artist.email}")

        if not exact_matches.exists():
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(email__icontains=search)
            )
        else:
            queryset = exact_matches

        for artist in queryset:
            print(f"[Artist Search Debug] Найден артист: username={artist.user.username if artist.user else 'None'}, email={artist.email}")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        if 'img_cover_url' in request.data and request.data['img_cover_url'] == '':
            request.data['img_cover_url'] = None
        
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request, *args, **kwargs):
        if 'img_cover_url' in request.data and request.data['img_cover_url'] == '':
            request.data['img_cover_url'] = None
        
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        artist = self.get_object()
        albums = Album.objects.filter(artist=artist)
        serializer = AlbumSerializer(albums, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        artist = self.get_object()
        tracks = artist.tracks.all()
        serializer = TrackSerializer(tracks, many=True, context={'request': request})
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
        serializer = TrackSerializer(tracks, many=True, context={'request': request})
        return Response(serializer.data)


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = AlbumFilter
    search_fields = ['title', 'artist__user__username']
    ordering_fields = ['release_date', 'total_tracks', 'total_duration']

    def get_queryset(self):
        queryset = Album.objects.all()
        
        title = self.request.query_params.get('title', None)
        artist = self.request.query_params.get('artist', None)
        genre = self.request.query_params.get('genre', None)
        year = self.request.query_params.get('year', None)
        
        if title:
            queryset = queryset.filter(title__icontains=title)
        if artist:
            queryset = queryset.filter(
                Q(artist__user__username__icontains=artist) | 
                Q(artist__bio__icontains=artist)
            )
        if genre:
            queryset = queryset.filter(genres__title__icontains=genre)
        if year:
            queryset = queryset.filter(release_date__year=year)
            
        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        """Создает альбом и связывает его с пользователем"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        album = serializer.save()
        
        user = request.user
        
        UserAlbum.objects.create(
            user=user,
            album=album,
            position=UserAlbum.objects.filter(user=user).count() + 1,
            added_at=timezone.now()
        )
        
        genre_ids = request.data.get('genre_ids', [])
        if genre_ids:
            for genre_id in genre_ids:
                try:
                    genre = Genre.objects.get(id=genre_id)
                    AlbumGenre.objects.create(album=album, genre=genre)
                except Genre.DoesNotExist:
                    pass
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        album = self.get_object()
        tracks = album.tracks.all()
        serializer = TrackSerializer(tracks, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def genres(self, request, pk=None):
        album = self.get_object()
        genres = Genre.objects.filter(albums=album)
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        album = self.get_object()
        
        album.likes_count += 1
        album.save()

        try:
            user = request.user
            existing_activity = UserActivity.objects.filter(
                user=user,
                activity_type='like_album',
                album=album
            ).first()
            
            if existing_activity:
                activity_serializer = UserActivitySerializer(existing_activity)
                return Response({
                    'album': self.get_serializer(album).data,
                    'activity': activity_serializer.data,
                    'message': 'Existing activity found'
                })
            
            activity = UserActivity.objects.create(
                user=user,
                activity_type='like_album',
                album=album
            )
            
            if not activity.album:
                activity.album = album
                activity.save()
            
            activity_serializer = UserActivitySerializer(activity)
            
            
            return Response({
                'album': self.get_serializer(album).data,
                'activity': activity_serializer.data
            })
        except Exception as e:
            print(f"Ошибка при создании активности: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'album': self.get_serializer(album).data,
                'error': str(e)
            })
    
    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        album = self.get_object()
        
        if album.likes_count > 0:
            album.likes_count -= 1
            album.save()
        
        try:
            user = request.user
            deleted, _ = UserActivity.objects.filter(
                user=user,
                activity_type='like_album',
                album=album
            ).delete()
            
            
            return Response({
                'album': self.get_serializer(album).data,
                'status': 'unliked'
            })
        except Exception as e:
            return Response(self.get_serializer(album).data)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TrackFilter
    search_fields = ['title', 'artist__user__username', 'album__title']
    ordering_fields = ['release_date', 'play_count', 'likes_count', 'duration', 'avg_rating']

    def get_queryset(self) -> QuerySet[Track]:
        """
        Возвращает базовый queryset треков для работы фильтрации.
        """
        return Track.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Получает список треков с применением фильтрации, аннотаций и предзагрузки связанных данных.
        """
        queryset = self.filter_queryset(get_optimized_tracks_queryset(request))
        logger.info(f"TrackViewSet: Найдено {queryset.count()} треков")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """Возвращает аудиофайл для прослушивания"""
        track = self.get_object()
        
        if not track.audio_file:
            return Response({'error': 'Аудиофайл не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        response = FileResponse(track.audio_file, content_type='audio/mpeg')
        response['Content-Disposition'] = f'inline; filename="{track.title}.mp3"'
        return response

    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        track = self.get_object()
        track.play_count += 1
        track.save()

        try:
            user = request.user
            activity = UserActivity.objects.create(
                user=user,
                activity_type='play',
                track=track,
                duration=request.data.get('duration', track.duration)
            )
            
            if track.album:
                album_activity = UserActivity.objects.create(
                    user=user,
                    activity_type='play',
                    album=track.album,
                    duration=request.data.get('duration', track.duration)
                )
            
            activity_serializer = UserActivitySerializer(activity, context={'request': request})
            
            artist = track.artist
            artist.monthly_listeners += 1
            artist.save()
            
            return Response({
                'track': self.get_serializer(track).data,
                'activity': activity_serializer.data
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(self.get_serializer(track).data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        track = self.get_object()
        
        track.likes_count += 1
        track.save()

        try:
            user = request.user
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
        except Exception as e:
            print(f"Ошибка при создании активности: {str(e)}")
            return Response(self.get_serializer(track).data)
    
    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        track = self.get_object()
        
        if track.likes_count > 0:
            track.likes_count -= 1
            track.save()
        
        try:
            user = request.user
            deleted, _ = UserActivity.objects.filter(
                user=user,
                activity_type='like',
                track=track
            ).delete()
            
            
            return Response({
                'track': self.get_serializer(track).data,
                'status': 'unliked'
            })
        except Exception as e:
            print(f"Ошибка при удалении активности: {str(e)}")
            return Response(self.get_serializer(track).data)
    
    @action(detail=True, methods=['get'])
    def genres(self, request, pk=None):
        track = self.get_object()
        genre_ids = track.genres.values_list('id', flat=True)
        genres = Genre.objects.filter(id__in=genre_ids)
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_name='genre-statistics', url_path='genre-statistics')
    def genre_statistics(self, request):
        """
        Получение статистики по жанрам
        """
        statistics = Track.objects.values('genres__title').annotate(
            track_count=Count('id'),
            total_duration=Sum('duration'),
            avg_plays=Avg('play_count'),
            avg_likes=Avg('likes_count')
        ).order_by('-track_count')
        
        return Response({
            'genre_statistics': list(statistics),
            'total_genres': len(statistics)
        })

    @action(detail=False, methods=['get'], url_name='popular-tracks', url_path='popular-tracks')
    def popular_tracks(self, request):
        """
        Получение популярных треков с рассчитанным рейтингом
        """
        limit = int(request.query_params.get('limit', 10))
        
        tracks = Track.objects.annotate(
            popularity_score=(F('play_count') + F('likes_count') * 2) / (1 + F('duration') / 300)
        ).values(
            'id', 'title', 'artist__user__username', 'artist__email',
            'play_count', 'likes_count', 'duration', 'popularity_score'
        ).order_by('-popularity_score')[:limit]
        
        return Response({
            'popular_tracks': list(tracks),
            'total_tracks': len(tracks)
        })

    @action(detail=False, methods=['get'], url_name='top-artists', url_path='top-artists')
    def top_artists(self, request):
        """
        Получение топ исполнителей по длительности контента
        """
        limit = int(request.query_params.get('limit', 10))
        
        artists = Track.objects.values('artist__email', 'artist__user__username').annotate(
            total_tracks=Count('id'),
            total_duration=Sum('duration'),
            avg_duration=Avg('duration'),
            total_plays=Sum('play_count')
        ).order_by('-total_duration')[:limit]
        
        return Response({
            'top_artists': list(artists),
            'total_artists': len(artists)
        })


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = PlaylistFilter
    search_fields = ['title', 'user__username']
    ordering_fields = ['creation_date', 'total_tracks', 'total_duration']

    @log_query_performance
    def get_queryset(self) -> QuerySet[Playlist]:
        """
        Получает queryset плейлистов с учетом фильтрации по пользователю и публичности.

        Returns:
            QuerySet[Playlist]: Отфильтрованный queryset плейлистов
        """
        queryset = Playlist.objects.select_related(
            'user'
        ).prefetch_related(
            'tracks',
            Prefetch('tracks__artist'),
            Prefetch('tracks__album')
        )
        
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            queryset = queryset.filter(
                Q(is_public=True) | Q(user__id=user_id)
            )
        else:
            queryset = queryset.filter(is_public=True)
        
        exclude_empty = self.request.query_params.get('exclude_empty', False)
        if exclude_empty and str(exclude_empty).lower() == 'true':
            queryset = queryset.exclude(total_tracks=0)
        
        logger.info(f"PlaylistViewSet: Найдено {queryset.count()} плейлистов")
        return queryset

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        playlist = self.get_object()
        track_ids = PlaylistTrack.objects.filter(playlist=playlist).order_by('position').values_list('track_id', flat=True)
        tracks = Track.objects.filter(id__in=track_ids)
        serializer = TrackSerializer(tracks, many=True)
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
        
        max_position = PlaylistTrack.objects.filter(playlist=playlist).values_list('position', flat=True).order_by('-position').first()
        position = (max_position + 1) if max_position else 1
        
        playlist_track = PlaylistTrack.objects.create(
            playlist=playlist,
            track=track,
            position=position
        )
        
        playlist.total_tracks = PlaylistTrack.objects.filter(playlist=playlist).count()
        playlist.total_duration += track.duration
        playlist.save()
        
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
        
        playlist.total_tracks -= 1
        playlist.total_duration -= track.duration
        playlist.save()
        
        playlist_track.delete()
        
        track_ids = PlaylistTrack.objects.filter(playlist=playlist).order_by('position').values_list('id', flat=True)
        for position, track_id in enumerate(track_ids, 1):
            PlaylistTrack.objects.filter(id=track_id).update(position=position)
        
        return Response({'status': 'track removed from playlist'})

    def update(self, request, *args, **kwargs):
        playlist = self.get_object()
        if playlist.user != request.user and not request.user.is_staff:
            return Response({'error': 'Вы не являетесь владельцем этого плейлиста.'}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        playlist = self.get_object()
        if playlist.user != request.user and not request.user.is_staff:
            return Response({'error': 'Вы не являетесь владельцем этого плейлиста.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        playlist = self.get_object()
        if playlist.user != request.user and not request.user.is_staff:
            return Response({'error': 'Вы не являетесь владельцем этого плейлиста.'}, status=403)
        return super().destroy(request, *args, **kwargs)


class UserActivityViewSet(viewsets.ModelViewSet):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = UserActivityFilter
    search_fields = ['user__username', 'activity_type']
    ordering_fields = ['timestamp']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        # Базовый QuerySet с предзагрузкой связанных данных
        queryset = UserActivity.objects.select_related(
            'user',
            'track',
            'track__artist',
            'track__album',
            'album',
            'album__artist',
            'artist'
        )
        
        # Фильтруем по пользователю, если указан user_id
        user_id = self.request.query_params.get('user_id')
        if user_id:
            # Проверяем права доступа
            if str(self.request.user.id) != str(user_id) and not self.request.user.is_staff:
                return UserActivity.objects.none()
            queryset = queryset.filter(user_id=user_id)
        else:
            # Если user_id не указан, показываем только активности текущего пользователя
            queryset = queryset.filter(user=self.request.user)
        
        # Фильтруем по типу активности, если указан
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Сортируем по времени
        queryset = queryset.order_by('-timestamp')
        
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

    def get_queryset(self) -> QuerySet[UserSubscribe]:
        """
        Получает queryset подписок пользователя с фильтрацией по user_id.

        Returns:
            QuerySet[UserSubscribe]: Отфильтрованный queryset подписок пользователя
        """
        queryset = UserSubscribe.objects.all()
        
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

    def get_queryset(self) -> QuerySet[UserAlbum]:
        """
        Получает queryset альбомов пользователя с фильтрацией по user_id.

        Returns:
            QuerySet[UserAlbum]: Отфильтрованный queryset альбомов пользователя
        """
        queryset = UserAlbum.objects.all()
        
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

    def get_queryset(self) -> QuerySet[UserTrack]:
        """
        Получает queryset треков пользователя с фильтрацией по user_id.

        Returns:
            QuerySet[UserTrack]: Отфильтрованный queryset треков пользователя
        """
        queryset = UserTrack.objects.all()
        
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

    def get_queryset(self) -> QuerySet[PlaylistTrack]:
        """
        Получает queryset связей плейлист-трек с фильтрацией по playlist_id.

        Returns:
            QuerySet[PlaylistTrack]: Отфильтрованный queryset связей плейлист-трек
        """
        queryset = PlaylistTrack.objects.all()
        
        playlist_id = self.request.query_params.get('playlist_id', None)
        if playlist_id is not None:
            queryset = queryset.filter(playlist__id=playlist_id)
        
        return queryset


class AlbumGenreViewSet(viewsets.ModelViewSet):
    queryset = AlbumGenre.objects.all()
    serializer_class = AlbumGenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['album__title', 'genre__title']

    def get_queryset(self) -> QuerySet[AlbumGenre]:
        """
        Получает queryset связей альбом-жанр с фильтрацией по album_id и genre_id.

        Returns:
            QuerySet[AlbumGenre]: Отфильтрованный queryset связей альбом-жанр
        """
        queryset = AlbumGenre.objects.all()
        
        album_id = self.request.query_params.get('album_id', None)
        if album_id is not None:
            queryset = queryset.filter(album__id=album_id)
        
        genre_id = self.request.query_params.get('genre_id', None)
        if genre_id is not None:
            queryset = queryset.filter(genre__id=genre_id)
        
        return queryset


class TrackGenreViewSet(viewsets.ModelViewSet):
    queryset = TrackGenre.objects.all()
    serializer_class = TrackGenreSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['track__title', 'genre__title']

    def get_queryset(self) -> QuerySet[TrackGenre]:
        """
        Получает queryset связей трек-жанр с фильтрацией по track_id и genre_id.

        Returns:
            QuerySet[TrackGenre]: Отфильтрованный queryset связей трек-жанр
        """
        queryset = TrackGenre.objects.all()
        
        track_id = self.request.query_params.get('track_id', None)
        if track_id is not None:
            queryset = queryset.filter(track__id=track_id)
        
        genre_id = self.request.query_params.get('genre_id', None)
        if genre_id is not None:
            queryset = queryset.filter(genre__id=genre_id)
        
        return queryset


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
        
    try:
        user = User.objects.get(username=username)
        
        if user.check_password(password):
            token, created = Token.objects.get_or_create(user=user)
            serializer = UserSerializer(user, context={'request': request})
            return Response({
                'token': token.key,
                'user': serializer.data
            })
        else:
            return Response({
                'error': 'Неверный пароль'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        print(f"Пользователь не найден: {username}")
        return Response({
            'error': 'Пользователь не найден'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Необходимо указать имя пользователя и пароль'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'Пользователь с таким именем уже существует'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='user'
    )
    
    token = Token.objects.create(user=user)
    
    return Response({
        'message': 'Пользователь успешно зарегистрирован',
        'token': token.key
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_track_view(request):
    
    title = request.data.get('title')
    artist_id = request.data.get('artist_id')
    album_id = request.data.get('album_id')
    track_number = request.data.get('track_number')
    duration = request.data.get('duration')
    genre_ids = request.data.getlist('genre_ids')
    audio_file = request.FILES.get('audio_file')
    
    if not all([title, artist_id, album_id, track_number, duration, audio_file]):
        return Response({
            'error': 'Не все обязательные поля заполнены'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        artist = get_object_or_404(Artist, id=artist_id)
        album = get_object_or_404(Album, id=album_id)
        
        track = Track.objects.create(
            title=title,
            artist=artist,
            album=album,
            track_number=track_number,
            release_date=album.release_date,
            duration=duration,
            audio_file=audio_file
        )
        
        if genre_ids:
            for genre_id in genre_ids:
                genre = get_object_or_404(Genre, id=genre_id)
                TrackGenre.objects.create(track=track, genre=genre)
        
        album.total_tracks = Track.objects.filter(album=album).count()
        album.total_duration = Track.objects.filter(album=album).aggregate(
            total=Sum('duration'))['total'] or 0
        album.save()
        
        serializer = TrackSerializer(track)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfilePhotoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        user = request.user
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=400)

        file = request.FILES['file']
        
        # Сохраняем в новое поле
        user.profile_image = file
        # Сохраняем URL для обратной совместимости
        user.img_profile_url = request.build_absolute_uri(user.profile_image.url)
        user.save()

        return Response({
            'message': 'Profile photo uploaded successfully',
            'url': user.img_profile_url
        })


class ArtistPhotoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        """Загрузка изображения исполнителя"""
        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if 'artist_id' not in request.data:
            return Response({
                'error': 'ID исполнителя не указан'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image = request.FILES['image']
        artist_id = request.data['artist_id']
        
        try:
            artist = Artist.objects.get(id=artist_id)
            
            if artist.email != request.user.email:
                return Response({
                    'error': 'У вас нет прав для редактирования этого исполнителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            artist_images_dir = os.path.join(settings.MEDIA_ROOT, 'artist_images')
            if not os.path.exists(artist_images_dir):
                os.makedirs(artist_images_dir)
            
            filename = f"artist_{artist.id}_{image.name}"
            filepath = os.path.join(artist_images_dir, filename)
            
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            cover_image_url = f"{settings.MEDIA_URL}artist_images/{filename}"
            artist.cover_image = image
            artist.save()
            
            return Response({
                'cover_image_url': cover_image_url
            }, status=status.HTTP_200_OK)
        
        except Artist.DoesNotExist:
            return Response({
                'error': 'Исполнитель не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_tracks(request):
    """Получение последних добавленных треков"""
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    
    tracks = Track.objects.all().order_by('-id')[:limit]
    serializer = TrackSerializer(tracks, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_albums(request):
    """Получение последних добавленных альбомов"""
    limit = request.query_params.get('limit', 10)
    exclude_empty = request.query_params.get('exclude_empty', 'false').lower() == 'true'
    
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    
    albums = Album.objects.all()
    
    if exclude_empty:
        albums = albums.exclude(total_tracks=0)
    
    albums = albums.order_by('-id')[:limit]
    serializer = AlbumSerializer(albums, many=True, context={'request': request})
    return Response(serializer.data)


class StatisticsViewSet(viewsets.ViewSet):
    """ViewSet для работы со статистикой"""
    
    permission_classes = [IsAuthenticated]
    queryset = Statistics.objects.all()
    
    def list(self, request):
        """
        Возвращает URLs для всех типов статистики
        """
        statistics = Statistics()
        serializer = StatisticsSerializer(statistics)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return self.queryset.all()
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]


class TrackReviewViewSet(ReviewViewSet):
    queryset = TrackReview.objects.all()
    serializer_class = TrackReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @log_query_performance
    def get_queryset(self):
        logger.info("TrackReviewViewSet: Начало получения отзывов")
        # Оптимизированный запрос с использованием select_related
        queryset = TrackReview.objects.select_related(
            'author',
            'track',
            'track__artist',
            'track__album'
        )
        
        track_id = self.request.query_params.get('track_id')
        if track_id:
            queryset = queryset.filter(track_id=track_id)
        
        logger.info(f"TrackReviewViewSet: Найдено {queryset.count()} отзывов")
        return queryset

    def perform_create(self, serializer):
        logger.info(f"TrackReviewViewSet: Создание отзыва. Данные: {serializer.validated_data}")
        serializer.save(author=self.request.user)
        logger.info(f"TrackReviewViewSet: Отзыв успешно создан")

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация отзыва на трек.
        Проверяет, что пользователь не оставлял отзыв на этот трек ранее
        и что он действительно прослушивал этот трек.
        """
        user = self.context['request'].user
        track = data.get('track')

        # Проверка на уникальность отзыва
        if TrackReview.objects.filter(author=user, track=track).exists():
            raise serializers.ValidationError(
                'Вы уже оставляли отзыв на этот трек'
            )

        # Проверка на факт прослушивания
        has_play = UserActivity.objects.filter(user=user, track=track, activity_type='play').exists()
        if not has_play:
            raise serializers.ValidationError(
                'Вы не можете оставить отзыв на трек, который не прослушивали.'
            )

        return data


class AlbumReviewViewSet(ReviewViewSet):
    queryset = AlbumReview.objects.all()
    serializer_class = AlbumReviewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        album_id = self.request.query_params.get('album_id')
        if album_id:
            queryset = queryset.filter(album_id=album_id)
        return queryset 

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_tracks_analytics(request):
    time_range = request.GET.get("time_range", "week")
    now = timezone.now()

    if time_range == "week":
        start_date = now - timedelta(days=7)
    elif time_range == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)

    tracks = Track.objects.annotate(
        total_plays=Count(
            "user_activities",
            filter=Q(
                user_activities__activity_type="play",
                user_activities__timestamp__gte=start_date
            )
        ),
        calculated_avg_rating=Avg("reviews__rating"),
        review_count=Count("reviews")
    ).filter(total_plays__gt=0).order_by("-total_plays")[:10]

    data = [
        {
            "title": track.title,
            "play_count": track.total_plays,
            "avg_rating": round(track.calculated_avg_rating, 2) if track.calculated_avg_rating else 0,
            "review_count": track.review_count,
            "artist": track.artist.user.username if track.artist else "Неизвестный исполнитель"
        }
        for track in tracks
    ]

    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_activity(request):
    time_range = request.GET.get("time_range", "week")
    now = timezone.now()

    if time_range == "week":
        start_date = now - timedelta(days=7)
        interval = "day"
    elif time_range == "month":
        start_date = now - timedelta(days=30)
        interval = "day"
    else:  # year
        start_date = now - timedelta(days=365)
        interval = "month"

    # Получаем активных пользователей
    active_users = User.objects.filter(
        last_login__gte=start_date
    ).annotate(
        date=TruncDate("last_login")
    ).values("date").annotate(
        count=Count("id")
    ).order_by("date")

    # Получаем новых пользователей
    new_users = User.objects.filter(
        date_joined__gte=start_date
    ).annotate(
        date=TruncDate("date_joined")
    ).values("date").annotate(
        count=Count("id")
    ).order_by("date")

    # Объединяем данные
    dates = set()
    for item in active_users:
        dates.add(item["date"])
    for item in new_users:
        dates.add(item["date"])

    data = []
    for date in sorted(dates):
        active_count = next(
            (item["count"] for item in active_users if item["date"] == date),
            0
        )
        new_count = next(
            (item["count"] for item in new_users if item["date"] == date),
            0
        )
        data.append({
            "date": date,
            "active_users": active_count,
            "new_users": new_count
        })

    return Response(data) 

def get_optimized_tracks_queryset(request, filters=None):
    qs = Track.objects.select_related(
        'artist',
        'album'
    ).prefetch_related(
        'genres',
        Prefetch('trackgenre_set', queryset=TrackGenre.objects.select_related('genre'))
    ).annotate(
        calculated_avg_rating=Avg('reviews__rating'),
        total_plays=Count('user_activities', filter=Q(user_activities__activity_type='play'))
    )
    if filters:
        qs = qs.filter(**filters)
    return qs

class OptimizedTrackListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        queryset = get_optimized_tracks_queryset(request)
        serializer = TrackSerializer(queryset, many=True, context={'request': request})
        return Response({'status': 'success', 'data': serializer.data})

class OptimizedPlaylistListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Оптимизированное получение плейлистов с информацией о пользователях
        """
        logger.info("OptimizedPlaylistListView: Получение плейлистов")
        try:
            playlists = Playlist.objects.select_related(
                'user'
            ).prefetch_related(
                'tracks',
                Prefetch('tracks__artist'),
                Prefetch('tracks__album')
            ).filter(user=request.user)
            
            logger.info(f"OptimizedPlaylistListView: Найдено {playlists.count()} плейлистов")
            
            serializer = PlaylistSerializer(playlists, many=True, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OptimizedPlaylistListView: Ошибка при получении плейлистов - {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OptimizedUserReviewsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Оптимизированное получение отзывов пользователя с информацией о треках
        """
        logger.info("OptimizedUserReviewsView: Получение отзывов пользователя")
        try:
            reviews = TrackReview.objects.select_related(
                'author',
                'track',
                'track__artist',
                'track__album'
            ).filter(author=request.user)
            
            logger.info(f"OptimizedUserReviewsView: Найдено {reviews.count()} отзывов")
            
            serializer = TrackReviewSerializer(reviews, many=True, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OptimizedUserReviewsView: Ошибка при получении отзывов - {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 