from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from kaudio.models import User, Artist, Album, Genre, Track, TrackGenre, AlbumGenre, UserAlbum, UserTrack, Playlist, Review
from kaudio.serializers import TrackSerializer
from django.conf import settings
from django.db.models import Sum, Prefetch
from django.shortcuts import get_object_or_404
import os
from django.utils import timezone

class PlaylistSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ['id', 'name', 'user', 'tracks', 'created_at']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }

class ReviewSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'track', 'rating', 'comment', 'created_at']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }

class ProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        """Загрузка изображения профиля пользователя"""
        print("ProfileImageUploadView вызван")
        print(f"FILES: {request.FILES}")
        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image = request.FILES['image']
        user = request.user
        
        # Сохраняем изображение через ImageField
        user.profile_image = image
        user.save()
        
        # Получаем URL через свойство img_profile_url
        profile_image_url = user.img_profile_url
        
        return Response({
            'img_profile_url': profile_image_url,
            'message': 'Изображение профиля успешно загружено'
        }, status=status.HTTP_200_OK)
        
    def options(self, request, *args, **kwargs):
        """
        Обработка CORS preflight запроса OPTIONS.
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class ArtistImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        """Загрузка изображения обложки исполнителя"""
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
            
            # Сохраняем изображение через ImageField
            artist.cover_image = image
            artist.save()
            
            # Получаем URL через свойство
            cover_image_url = artist.img_cover_url
            
            return Response({
                'img_cover_url': cover_image_url,
                'message': 'Изображение исполнителя успешно загружено'
            }, status=status.HTTP_200_OK)
            
        except Artist.DoesNotExist:
            return Response({
                'error': 'Исполнитель не найден'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            print(f"Ошибка при загрузке изображения исполнителя: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request, *args, **kwargs):
        """
        Обработка CORS preflight запроса OPTIONS.
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class TrackUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        """
        Загрузка нового трека и заполнение связанных таблиц.
        """
        print("TrackUploadView POST вызван")
        print(f"HTTP метод: {request.method}")
        print(f"FILES: {request.FILES}")
        print(f"DATA: {request.data}")
        
        # Получаем артиста только по текущему пользователю
        artist = Artist.objects.filter(user=request.user).first()
        if not artist:
            print("У пользователя нет профиля исполнителя")
            return Response({
                'error': 'У вас нет профиля исполнителя. Сначала создайте артиста.'
            }, status=status.HTTP_400_BAD_REQUEST)
        # album_id и остальные поля оставляем как есть
        album_id = request.data.get('album_id')
        track_number = request.data.get('track_number')
        duration = request.data.get('duration')
        genre_ids = request.data.getlist('genre_ids') if hasattr(request.data, 'getlist') else request.data.get('genre_ids', [])
        audio_file = request.FILES.get('audio_file')
        title = request.data.get('title')

        if not all([title, duration, audio_file]):
            print("Не все обязательные поля заполнены")
            return Response({
                'error': 'Не все обязательные поля заполнены'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            album = None
            user = request.user
            if album_id:
                album = get_object_or_404(Album, id=album_id)
                if not track_number:
                    return Response({
                        'error': 'При выборе альбома необходимо указать номер трека'
                    }, status=status.HTTP_400_BAD_REQUEST)
            track = Track.objects.create(
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
                    genre = get_object_or_404(Genre, id=genre_id)
                    
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
            print(f"Трек успешно создан: {track.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Ошибка при создании трека: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request, *args, **kwargs):
        """
        Обработка CORS preflight запроса OPTIONS.
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class AlbumImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, format=None):
        """Загрузка изображения обложки альбома"""
        print("AlbumImageUploadView вызван")
        print(f"FILES: {request.FILES}")
        print(f"DATA: {request.data}")
        
        if 'image' not in request.FILES:
            return Response({
                'error': 'Изображение не предоставлено'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if 'album_id' not in request.data:
            return Response({
                'error': 'ID альбома не указан'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        image = request.FILES['image']
        album_id = request.data['album_id']
        
        try:
            album = get_object_or_404(Album, id=album_id)
            
            if album.artist.email != request.user.email:
                return Response({
                    'error': 'У вас нет прав для редактирования этого альбома'
                }, status=status.HTTP_403_FORBIDDEN)
            
            album_images_dir = os.path.join(settings.MEDIA_ROOT, 'album_images')
            if not os.path.exists(album_images_dir):
                os.makedirs(album_images_dir)
            
            filename = f"album_{album.id}_{image.name}"
            filepath = os.path.join(album_images_dir, filename)
            
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            cover_image_url = f"{settings.MEDIA_URL}album_images/{filename}"
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
            print(f"Ошибка при загрузке изображения альбома: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def options(self, request, *args, **kwargs):
        """
        Обработка CORS preflight запроса OPTIONS.
        """
        response = Response()
        response['Allow'] = 'POST, OPTIONS'
        return response


class TrackListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Получение списка треков с оптимизированными запросами
        """
        try:
            tracks = Track.objects.select_related(
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Получение плейлистов с информацией о пользователях
        """
        try:
            playlists = Playlist.objects.select_related(
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """
        Получение отзывов пользователя с информацией о треках
        """
        try:
            reviews = Review.objects.select_related(
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