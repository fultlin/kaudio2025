from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, Avg, F, Prefetch
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

logger = logging.getLogger(__name__)

def log_query_performance(func):
    def wrapper(*args, **kwargs):
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'date_joined']
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        if 'img_profile_url' in request.data and request.data['img_profile_url'] == '':
            request.data['img_profile_url'] = None
        
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request, *args, **kwargs):
        if 'img_profile_url' in request.data and request.data['img_profile_url'] == '':
            request.data['img_profile_url'] = None
        
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def playlists(self, request, pk=None):
        user = self.get_object()
        playlists = Playlist.objects.filter(user=user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        try:
            user = self.get_object()
            print(f"[UserActivity Debug] Получение активностей для пользователя {user.username}")
            
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
            
            print(f"[UserActivity Debug] Найдено активностей: {activities.count()}")
            
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'bio']
    ordering_fields = ['monthly_listeners', 'is_verified']

    def get_queryset(self):
        queryset = Artist.objects.all()
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if Artist.objects.filter(user=user).exists():
            raise PermissionDenied('У вас уже есть профиль исполнителя.')
        serializer.save(user=user, username=user.username, email=user.email)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.user != self.request.user:
            raise PermissionDenied('Вы не можете редактировать чужой профиль исполнителя.')
        # Не позволяем менять username и email артиста
        serializer.save(username=instance.user.username, email=instance.user.email)

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')
        print(f"\n[Artist Search Debug] ====== НАЧАЛО ПОИСКА АРТИСТОВ ======")
        print(f"[Artist Search Debug] Поисковый запрос: '{search}'")
        
        if not search:
            return super().list(request, *args, **kwargs)

        queryset = Artist.objects.select_related('user').all()
        print(f"[Artist Search Debug] Всего артистов в базе: {queryset.count()}")

        exact_matches = queryset.filter(
            Q(user__username__iexact=search) |
            Q(email__iexact=search)
        )
        print(f"[Artist Search Debug] Найдено точных совпадений: {exact_matches.count()}")
        for artist in exact_matches:
            print(f"[Artist Search Debug] Точное совпадение: username={artist.user.username if artist.user else 'None'}, email={artist.email}")

        if not exact_matches.exists():
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(email__icontains=search)
            )
        else:
            queryset = exact_matches

        print(f"[Artist Search Debug] Итоговое количество результатов: {queryset.count()}")
        for artist in queryset:
            print(f"[Artist Search Debug] Найден артист: username={artist.user.username if artist.user else 'None'}, email={artist.email}")
        print(f"[Artist Search Debug] ====== КОНЕЦ ПОИСКА АРТИСТОВ ======\n")

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = Artist.objects.select_related('user').all()
        search = self.request.query_params.get('search', None)
        
        if search:
            search = search.lower()
            print(f"[Artist Search Debug] Поисковый запрос (в нижнем регистре): {search}")
            
            queryset = queryset.annotate(
                username_lower=Lower('user__username')
            ).filter(username_lower__contains=search)
            
            print(f"[Artist Search Debug] SQL: {str(queryset.query)}")
            artists = list(queryset)
            print(f"[Artist Search Debug] Найдено артистов: {len(artists)}")
            for artist in artists:
                print(f"[Artist Search Debug] Артист: {artist.user.username if artist.user else 'No username'}")
        
        return queryset.distinct()

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

    def get_queryset(self):
        queryset = Album.objects.all()
        
        # Получаем параметры запроса
        title = self.request.query_params.get('title', None)
        artist = self.request.query_params.get('artist', None)
        genre = self.request.query_params.get('genre', None)
        year = self.request.query_params.get('year', None)
        
        # Применяем фильтры
        if title:
            queryset = queryset.filter(title__icontains=title)
        if artist:
            queryset = queryset.filter(
                Q(artist__email__icontains=artist) | 
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
        tracks = Track.objects.filter(album=album)
        serializer = TrackSerializer(tracks, many=True)
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
        print(f"Добавление лайка альбома {album.id} пользователем {request.user.username} (ID: {request.user.id})")
        
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
                print(f"Активность 'like_album' уже существует: ID={existing_activity.id}")
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
                print(f"ВНИМАНИЕ: Альбом не сохранен в активности, исправляем...")
                activity.album = album
                activity.save()
            
            activity_serializer = UserActivitySerializer(activity)
            
            print(f"Активность 'like_album' создана: ID={activity.id}, связана с альбомом ID={activity.album.id if activity.album else None}")
            
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
        print(f"Удаление лайка у альбома {album.id} пользователем {request.user.username} (ID: {request.user.id})")
        
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
            
            print(f"Удалено активностей: {deleted}")
            
            return Response({
                'album': self.get_serializer(album).data,
                'status': 'unliked'
            })
        except Exception as e:
            print(f"Ошибка при удалении активности: {str(e)}")
            return Response(self.get_serializer(album).data)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    ordering_fields = ['release_date', 'play_count', 'likes_count', 'duration']

    @log_query_performance
    def get_queryset(self):
        logger.info("TrackViewSet: Начало получения списка треков")
        # Оптимизированный запрос с использованием select_related и prefetch_related
        queryset = Track.objects.select_related(
            'artist',
            'artist__user',
            'album'
        ).prefetch_related(
            'genres',
            Prefetch('trackgenre_set', queryset=TrackGenre.objects.select_related('genre'))
        ).annotate(
            calculated_avg_rating=Avg('reviews__rating'),
            total_plays=Count('user_activities', filter=Q(user_activities__activity_type='play'))
        )
        
        # Получаем параметры запроса
        title = self.request.query_params.get('title', None)
        artist = self.request.query_params.get('artist', None)
        album = self.request.query_params.get('album', None)
        genre = self.request.query_params.get('genre', None)
        year = self.request.query_params.get('year', None)
        
        # Применяем фильтры
        if title:
            queryset = queryset.filter(title__icontains=title)
        if artist:
            queryset = queryset.filter(
                Q(artist__user__username__icontains=artist) |
                Q(artist__email__icontains=artist)
            )
        if album:
            queryset = queryset.filter(album__title__icontains=album)
        if genre:
            queryset = queryset.filter(genres__title__icontains=genre)
        if year:
            queryset = queryset.filter(release_date__year=year)
        
        logger.info(f"TrackViewSet: Найдено {queryset.count()} треков")
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')
        print(f"\n[Search Debug] ====== НАЧАЛО ПОИСКА ТРЕКОВ ======")
        print(f"[Search Debug] Поисковый запрос: '{search}'")
        
        if not search:
            return super().list(request, *args, **kwargs)

        # Получаем базовый queryset
        queryset = self.get_queryset()
        print(f"[Search Debug] Всего треков в базе: {queryset.count()}")

        # Поиск по нику пользователя
        user_tracks = queryset.filter(artist__user__username__icontains=search)
        print(f"[Search Debug] Найдено треков по нику пользователя: {user_tracks.count()}")
        
        # Используем values() для логирования
        user_tracks_info = user_tracks.values('title', 'artist__user__username', 'artist__email')
        for track in user_tracks_info:
            print(f"[Search Debug] Трек по нику: {track['title']} | Артист: username={track['artist__user__username']}")

        # Поиск по email артиста
        email_tracks = queryset.filter(artist__email__icontains=search)
        print(f"[Search Debug] Найдено треков по email артиста: {email_tracks.count()}")
        
        # Используем values() для логирования
        email_tracks_info = email_tracks.values('title', 'artist__email')
        for track in email_tracks_info:
            print(f"[Search Debug] Трек по email: {track['title']} | Артист: email={track['artist__email']}")

        # Поиск по названию трека
        title_tracks = queryset.filter(title__icontains=search)
        print(f"[Search Debug] Найдено по названию трека: {title_tracks.count()}")
        
        # Используем values() для логирования
        title_tracks_info = title_tracks.values('title')
        for track in title_tracks_info:
            print(f"[Search Debug] Трек по названию: {track['title']}")

        # Объединяем все результаты
        queryset = user_tracks | email_tracks | title_tracks
        queryset = queryset.distinct()
        
        # Выводим итоговые результаты
        print(f"[Search Debug] Всего уникальных результатов: {queryset.count()}")
        
        # Используем values() для итогового логирования
        results_info = queryset.values('title', 'artist__user__username', 'artist__email')
        for track in results_info:
            artist_info = f"username={track['artist__user__username'] or 'None'}, email={track['artist__email'] or 'None'}"
            print(f"[Search Debug] Трек: {track['title']} | Артист: {artist_info}")
        print(f"[Search Debug] ====== КОНЕЦ ПОИСКА ТРЕКОВ ======\n")

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
            activity_serializer = UserActivitySerializer(activity)
            
            artist = track.artist
            artist.monthly_listeners += 1
            artist.save()
            
            return Response({
                'track': self.get_serializer(track).data,
                'activity': activity_serializer.data
            })
        except Exception as e:
            print(f"Ошибка при создании активности: {str(e)}")
            return Response(self.get_serializer(track).data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        track = self.get_object()
        print(f"Добавление лайка треку {track.id} пользователем {request.user.username} (ID: {request.user.id})")
        
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
            
            print(f"Активность 'like' создана: ID={activity.id}")
            
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
        print(f"Удаление лайка у трека {track.id} пользователем {request.user.username} (ID: {request.user.id})")
        
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
            
            print(f"Удалено активностей: {deleted}")
            
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
        # Используем values_list для получения только ID жанров
        genre_ids = track.genres.values_list('id', flat=True)
        genres = Genre.objects.filter(id__in=genre_ids)
        serializer = GenreSerializer(genres, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_name='genre-statistics', url_path='genre-statistics')
    def genre_statistics(self, request):
        """
        Получение статистики по жанрам
        """
        # Используем values() для агрегации данных
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
        
        # Используем values() для получения только нужных полей
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
        
        # Используем values() для агрегации данных по артистам
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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'user__username']
    ordering_fields = ['creation_date', 'total_tracks', 'total_duration']

    @log_query_performance
    def get_queryset(self):
        logger.info("PlaylistViewSet: Начало получения списка плейлистов")
        # Оптимизированный запрос с использованием select_related и prefetch_related
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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'activity_type']
    ordering_fields = ['timestamp']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(f"[UserActivityViewSet Debug] Получение активностей для пользователя {self.request.user.username}")
        
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
            print(f"[UserActivityViewSet Debug] Фильтрация по user_id: {user_id}")
            # Проверяем права доступа
            if str(self.request.user.id) != str(user_id) and not self.request.user.is_staff:
                print(f"[UserActivityViewSet Debug] Отказано в доступе: пользователь {self.request.user.username} пытается получить активности пользователя {user_id}")
                return UserActivity.objects.none()
            queryset = queryset.filter(user_id=user_id)
        else:
            # Если user_id не указан, показываем только активности текущего пользователя
            queryset = queryset.filter(user=self.request.user)
        
        # Фильтруем по типу активности, если указан
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            print(f"[UserActivityViewSet Debug] Фильтрация по activity_type: {activity_type}")
            queryset = queryset.filter(activity_type=activity_type)
        
        # Сортируем по времени
        queryset = queryset.order_by('-timestamp')
        
        print(f"[UserActivityViewSet Debug] Найдено активностей: {queryset.count()}")
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

    def get_queryset(self):
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
        role='user'  # Явно устанавливаем роль пользователя
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
    print("Вызван upload_track!")
    print(f"HTTP метод: {request.method}")
    print(f"FILES: {request.FILES}")
    print(f"DATA: {request.data}")
    
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
        print("ArtistImageUploadView POST вызван.")
        print(f"FILES: {request.FILES}")
        print(f"DATA: {request.data}")
        
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

    tracks = Track.objects.filter(
        release_date__gte=start_date
    ).annotate(
        total_plays=Count("user_activities", filter=Q(user_activities__activity_type="play")),
        avg_rating=Avg("reviews__rating"),
        review_count=Count("reviews")
    ).order_by("-total_plays")[:10]

    data = [
        {
            "title": track.title,
            "play_count": track.total_plays,
            "avg_rating": round(track.avg_rating, 2) if track.avg_rating else 0,
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

class OptimizedTrackListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Оптимизированное получение списка треков с альбомами и исполнителями
        """
        logger.info("OptimizedTrackListView: Получение списка треков")
        try:
            tracks = Track.objects.select_related(
                'artist',
                'album'
            ).prefetch_related(
                'genres',
                Prefetch('trackgenre_set', queryset=TrackGenre.objects.select_related('genre'))
            ).all()
            
            logger.info(f"OptimizedTrackListView: Найдено {tracks.count()} треков")
            
            serializer = TrackSerializer(tracks, many=True, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OptimizedTrackListView: Ошибка при получении треков - {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                'user',
                'track',
                'track__artist',
                'track__album'
            ).filter(user=request.user)
            
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