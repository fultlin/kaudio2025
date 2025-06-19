from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.request import Request
from kaudio.models import User, Artist, Album, Genre, Track, TrackGenre, AlbumGenre, UserAlbum, UserTrack, Playlist, Review
from kaudio.serializers import TrackSerializer
from django.conf import settings
from django.db.models import Sum, Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
import os
from django.utils import timezone
from typing import Dict, List, Any, Optional, Union
from django.core.files.uploadedfile import UploadedFile

class PlaylistSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Playlist.
    
    Предоставляет полную информацию о плейлисте включая треки и пользователя.
    """
    tracks = TrackSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ['id', 'name', 'user', 'tracks', 'created_at']
    
    def get_user(self, obj: Playlist) -> Dict[str, Any]:
        """
        Получает информацию о пользователе плейлиста.
        
        Args:
            obj: Объект плейлиста
            
        Returns:
            Dict[str, Any]: Словарь с информацией о пользователе
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }

class ReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Review.
    
    Предоставляет полную информацию об отзыве включая трек и пользователя.
    """
    track = TrackSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'track', 'rating', 'comment', 'created_at']
    
    def get_user(self, obj: Review) -> Dict[str, Any]:
        """
        Получает информацию о пользователе, оставившем отзыв.
        
        Args:
            obj: Объект отзыва
            
        Returns:
            Dict[str, Any]: Словарь с информацией о пользователе
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }

class ProfileImageUploadView(APIView):
    """
    API представление для загрузки изображения профиля пользователя.
    
    Позволяет аутентифицированным пользователям загружать изображения профиля.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает POST запрос для загрузки изображения профиля.
        
        Args:
            request: HTTP запрос с файлом изображения
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ с URL изображения или ошибкой
        """

        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image: UploadedFile = request.FILES['image']
        user: User = request.user
        
        # Сохраняем изображение через ImageField
        user.profile_image = image
        user.save()
        
        # Получаем URL через свойство img_profile_url
        profile_image_url: str = user.img_profile_url
        
        return Response({
            'img_profile_url': profile_image_url,
            'message': 'Изображение профиля успешно загружено'
        }, status=status.HTTP_200_OK)
        
    def options(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обработка CORS preflight запроса OPTIONS.
        
        Args:
            request: HTTP запрос
            *args: Дополнительные позиционные аргументы
            **kwargs: Дополнительные именованные аргументы
            
        Returns:
            Response: HTTP ответ с заголовками CORS
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class ArtistImageUploadView(APIView):
    """
    API представление для загрузки изображения обложки исполнителя.
    
    Позволяет исполнителям загружать изображения обложки для своих профилей.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает POST запрос для загрузки изображения исполнителя.
        
        Args:
            request: HTTP запрос с файлом изображения и ID исполнителя
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ с URL изображения или ошибкой
        """
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'artist_id' not in request.data:
            return Response({
                'error': 'ID исполнителя не указан'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image: UploadedFile = request.FILES['image']
        artist_id: int = request.data['artist_id']
        
        try:
            artist: Artist = Artist.objects.get(id=artist_id)
            
            if artist.email != request.user.email:
                return Response({
                    'error': 'У вас нет прав для редактирования этого исполнителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Сохраняем изображение через ImageField
            artist.cover_image = image
            artist.save()
            
            # Получаем URL через свойство
            cover_image_url: str = artist.img_cover_url
            
            return Response({
                'img_cover_url': cover_image_url,
                'message': 'Изображение исполнителя успешно загружено'
            }, status=status.HTTP_200_OK)
            
        except Artist.DoesNotExist:
            return Response({
                'error': 'Исполнитель не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обработка CORS preflight запроса OPTIONS.
        
        Args:
            request: HTTP запрос
            *args: Дополнительные позиционные аргументы
            **kwargs: Дополнительные именованные аргументы
            
        Returns:
            Response: HTTP ответ с заголовками CORS
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class TrackUploadView(APIView):
    """
    API представление для загрузки новых треков.
    
    Позволяет исполнителям загружать новые треки и связывать их с альбомами.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает POST запрос для загрузки нового трека.
        
        Создает новый трек, связывает его с жанрами и альбомом (если указан),
        а также добавляет в библиотеку пользователя.
        
        Args:
            request: HTTP запрос с данными трека и аудиофайлом
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ с данными созданного трека или ошибкой
        """
        
        artist: Optional[Artist] = Artist.objects.filter(user=request.user).first()
        if not artist:
            return Response({
                'error': 'У вас нет профиля исполнителя. Сначала создайте артиста.'
            }, status=status.HTTP_400_BAD_REQUEST)

        album_id: Optional[int] = request.data.get('album_id')
        track_number: Optional[int] = request.data.get('track_number')
        duration: Optional[int] = request.data.get('duration')
        genre_ids: List[int] = request.data.getlist('genre_ids') if hasattr(request.data, 'getlist') else request.data.get('genre_ids', [])
        audio_file: Optional[UploadedFile] = request.FILES.get('audio_file')
        title: Optional[str] = request.data.get('title')

        if not all([title, duration, audio_file]):
            return Response({
                'error': 'Не все обязательные поля заполнены'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            album: Optional[Album] = None
            user: User = request.user
            if album_id:
                album = get_object_or_404(Album, id=album_id)
                if not track_number:
                    return Response({
                        'error': 'При выборе альбома необходимо указать номер трека'
                    }, status=status.HTTP_400_BAD_REQUEST)
            track: Track = Track.objects.create(
                title=title,
                artist=artist,
                album=album,
                track_number=track_number if album else None,
                release_date=album.release_date if album else None,
                duration=duration,
                audio_file=audio_file
            )
            
            if genre_ids:
                for genre_id in genre_ids:
                    genre: Genre = get_object_or_404(Genre, id=genre_id)
                    
                    TrackGenre.objects.create(track=track, genre=genre)
                    
                    if album:
                        AlbumGenre.objects.get_or_create(album=album, genre=genre)
            
            if album:
                user_album, created = UserAlbum.objects.get_or_create(
                    user=user,
                    album=album,
                    defaults={
                        'position': UserAlbum.objects.filter(user=user).count() + 1,
                        'added_at': timezone.now()
                    }
                )
                
                album.total_tracks = Track.objects.filter(album=album).count()
                album.total_duration = Track.objects.filter(album=album).aggregate(
                    total=Sum('duration'))['total'] or 0
                album.save()
            
            UserTrack.objects.create(
                user=user,
                track=track,
                position=UserTrack.objects.filter(user=user).count() + 1,
                added_at=timezone.now()
            )
            
            serializer = TrackSerializer(track, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обработка CORS preflight запроса OPTIONS.
        
        Args:
            request: HTTP запрос
            *args: Дополнительные позиционные аргументы
            **kwargs: Дополнительные именованные аргументы
            
        Returns:
            Response: HTTP ответ с заголовками CORS
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class AlbumImageUploadView(APIView):
    """
    API представление для загрузки изображения обложки альбома.
    
    Позволяет исполнителям загружать изображения обложки для своих альбомов.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает POST запрос для загрузки изображения альбома.
        
        Args:
            request: HTTP запрос с файлом изображения и ID альбома
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ с URL изображения или ошибкой
        """

        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'album_id' not in request.data:
            return Response({
                'error': 'ID альбома не указан'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image: UploadedFile = request.FILES['image']
        album_id: int = request.data['album_id']
        
        try:
            album: Album = get_object_or_404(Album, id=album_id)
            
            if album.artist.email != request.user.email:
                return Response({
                    'error': 'У вас нет прав для редактирования этого альбома'
                }, status=status.HTTP_403_FORBIDDEN)
            
            album_images_dir: str = os.path.join(settings.MEDIA_ROOT, 'album_images')
            if not os.path.exists(album_images_dir):
                os.makedirs(album_images_dir)
            
            filename: str = f"album_{album.id}_{image.name}"
            filepath: str = os.path.join(album_images_dir, filename)
            
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            cover_image_url: str = f"{settings.MEDIA_URL}album_images/{filename}"
            album.img_url = cover_image_url
            album.save()
            
            return Response({
                'img_url': cover_image_url,
                'message': 'Изображение альбома успешно загружено'
            }, status=status.HTTP_200_OK)
        
        except Album.DoesNotExist:
            return Response({
                'error': 'Альбом не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Обработка CORS preflight запроса OPTIONS.
        
        Args:
            request: HTTP запрос
            *args: Дополнительные позиционные аргументы
            **kwargs: Дополнительные именованные аргументы
            
        Returns:
            Response: HTTP ответ с заголовками CORS
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class TrackListView(APIView):
    """
    API представление для получения списка треков.
    
    Предоставляет оптимизированный список всех треков с связанными данными.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает GET запрос для получения списка треков.
        
        Использует оптимизированные запросы для загрузки связанных данных.
        
        Args:
            request: HTTP запрос
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ со списком треков или ошибкой
        """
        try:
            tracks: QuerySet[Track] = Track.objects.select_related(
                'artist',
                'album'
            ).prefetch_related(
                'genres',
                Prefetch('trackgenre_set', queryset=TrackGenre.objects.select_related('genre'))
            ).all()
            
            serializer = TrackSerializer(tracks, many=True, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlaylistListView(APIView):
    """
    API представление для получения списка плейлистов пользователя.
    
    Предоставляет список плейлистов текущего пользователя с полной информацией.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает GET запрос для получения плейлистов пользователя.
        
        Args:
            request: HTTP запрос
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ со списком плейлистов или ошибкой
        """
        try:
            playlists: QuerySet[Playlist] = Playlist.objects.select_related(
                'user'
            ).prefetch_related(
                'tracks',
                Prefetch('tracks__artist'),
                Prefetch('tracks__album')
            ).filter(user=request.user)
            
            serializer = PlaylistSerializer(playlists, many=True, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserReviewsView(APIView):
    """
    API представление для получения отзывов пользователя.
    
    Предоставляет список отзывов, оставленных текущим пользователем.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """
        Обрабатывает GET запрос для получения отзывов пользователя.
        
        Args:
            request: HTTP запрос
            format: Формат ответа (опционально)
            
        Returns:
            Response: JSON ответ со списком отзывов или ошибкой
        """
        try:
            reviews: QuerySet[Review] = Review.objects.select_related(
                'user',
                'track',
                'track__artist',
                'track__album'
            ).filter(user=request.user)
            
            serializer = ReviewSerializer(reviews, many=True, context={'request': request})
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 