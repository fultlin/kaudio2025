from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.response import Response
from django.db.models import Q, Sum
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
from rest_framework.permissions import IsAuthenticated, AllowAny
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

logger = logging.getLogger(__name__)


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
        user = self.get_object()
        activities = user.activities.all()
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email']
    ordering_fields = ['monthly_listeners']

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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'artist__email', 'album__title']
    ordering_fields = ['release_date', 'play_count', 'likes_count', 'duration']

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
        
        max_position = PlaylistTrack.objects.filter(playlist=playlist).order_by('-position').first()
        position = (max_position.position + 1) if max_position else 1
        
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
        
        print(f"UserActivityViewSet.get_queryset вызван, авторизованный пользователь: {self.request.user}")
        
        if self.request.user.is_authenticated:
            print(f"Фильтруем активности для пользователя {self.request.user.username} (ID: {self.request.user.id})")
            queryset = queryset.filter(user=self.request.user)
        else:
            print("Пользователь не аутентифицирован")
        
        user_id = self.request.query_params.get('user_id', None)
        if user_id is not None:
            print(f"Дополнительная фильтрация по user_id: {user_id}")
            queryset = queryset.filter(user__id=user_id)
        
        activity_type = self.request.query_params.get('activity_type', None)
        if activity_type is not None:
            print(f"Фильтрация по activity_type: {activity_type}")
            queryset = queryset.filter(activity_type=activity_type)
        
        print(f"Итоговое количество записей: {queryset.count()}")
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
            serializer = UserSerializer(user)
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
        password=password
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
        """Загрузка изображения профиля пользователя"""
        print("ProfileImageUploadView POST вызван.")
        print(f"FILES: {request.FILES}")
        print(f"DATA: {request.data}")
        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image = request.FILES['image']
        user = request.user
        
        user_images_dir = os.path.join(settings.MEDIA_ROOT, 'profile_images')
        if not os.path.exists(user_images_dir):
            os.makedirs(user_images_dir)
        
        filename = f"profile_{user.id}_{image.name}"
        filepath = os.path.join(user_images_dir, filename)
        
        with open(filepath, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        profile_image_url = f"{settings.MEDIA_URL}profile_images/{filename}"
        user.img_profile_url = profile_image_url
        user.save()
        
        return Response({
            'img_profile_url': profile_image_url
        }, status=status.HTTP_200_OK)


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
            artist.img_cover_url = cover_image_url
            artist.save()
            
            return Response({
                'img_cover_url': cover_image_url
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
    serializer = TrackSerializer(tracks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_albums(request):
    """Получение последних добавленных альбомов"""
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    
    albums = Album.objects.all().order_by('-id')[:limit]
    serializer = AlbumSerializer(albums, many=True)
    return Response(serializer.data) 