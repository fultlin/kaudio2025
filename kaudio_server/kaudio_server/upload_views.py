from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from kaudio.models import User, Artist, Album, Genre, Track, TrackGenre
from kaudio.serializers import TrackSerializer
from django.conf import settings
from django.db.models import Sum
from django.shortcuts import get_object_or_404
import os

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
        
        # Создаем директорию для хранения изображений пользователей, если ее нет
        user_images_dir = os.path.join(settings.MEDIA_ROOT, 'profile_images')
        if not os.path.exists(user_images_dir):
            os.makedirs(user_images_dir)
        
        # Формируем имя файла, включая имя пользователя для уникальности
        filename = f"profile_{user.id}_{image.name}"
        filepath = os.path.join(user_images_dir, filename)
        
        # Сохраняем файл
        with open(filepath, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        # Обновляем ссылку на изображение у пользователя
        profile_image_url = f"{settings.MEDIA_URL}profile_images/{filename}"
        user.img_profile_url = profile_image_url
        user.save()
        
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
        print("ArtistImageUploadView вызван")
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
            # Получаем исполнителя и проверяем права доступа
            artist = Artist.objects.get(id=artist_id)
            
            # Проверяем, что email исполнителя совпадает с email пользователя
            if artist.email != request.user.email:
                return Response({
                    'error': 'У вас нет прав для редактирования этого исполнителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Создаем директорию для хранения изображений исполнителей, если ее нет
            artist_images_dir = os.path.join(settings.MEDIA_ROOT, 'artist_images')
            if not os.path.exists(artist_images_dir):
                os.makedirs(artist_images_dir)
            
            # Формируем имя файла
            filename = f"artist_{artist.id}_{image.name}"
            filepath = os.path.join(artist_images_dir, filename)
            
            # Сохраняем файл
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            # Обновляем ссылку на изображение у исполнителя
            cover_image_url = f"{settings.MEDIA_URL}artist_images/{filename}"
            artist.img_cover_url = cover_image_url
            artist.save()
            
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
        Загрузка нового трека.
        """
        print("TrackUploadView POST вызван")
        print(f"HTTP метод: {request.method}")
        print(f"FILES: {request.FILES}")
        print(f"DATA: {request.data}")
        
        # Получаем данные из запроса
        title = request.data.get('title')
        artist_id = request.data.get('artist_id')
        album_id = request.data.get('album_id')
        track_number = request.data.get('track_number')
        duration = request.data.get('duration')
        genre_ids = request.data.getlist('genre_ids') if hasattr(request.data, 'getlist') else request.data.get('genre_ids', [])
        audio_file = request.FILES.get('audio_file')
        
        # Проверяем обязательные поля
        if not all([title, artist_id, album_id, track_number, duration, audio_file]):
            print("Не все обязательные поля заполнены")
            return Response({
                'error': 'Не все обязательные поля заполнены'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Получаем связанные объекты
            artist = get_object_or_404(Artist, id=artist_id)
            album = get_object_or_404(Album, id=album_id)
            
            # Создаем трек
            track = Track.objects.create(
                title=title,
                artist=artist,
                album=album,
                track_number=track_number,
                release_date=album.release_date,  # Берем дату выпуска из альбома
                duration=duration,
                audio_file=audio_file
            )
            
            # Добавляем жанры, если они указаны
            if genre_ids:
                for genre_id in genre_ids:
                    genre = get_object_or_404(Genre, id=genre_id)
                    TrackGenre.objects.create(track=track, genre=genre)
            
            # Обновляем статистику альбома
            album.total_tracks = Track.objects.filter(album=album).count()
            album.total_duration = Track.objects.filter(album=album).aggregate(
                total=Sum('duration'))['total'] or 0
            album.save()
            
            # Возвращаем данные созданного трека
            serializer = TrackSerializer(track)
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