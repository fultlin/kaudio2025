from django.db import models
from django.utils import timezone
from django.db.models import Count, Sum, F, FloatField, ExpressionWrapper, Q, Avg, QuerySet
from typing import Optional, List, Dict, Any, Union


class UserActivityManager(models.Manager):
    """
    Менеджер для модели UserActivity.
    
    Предоставляет методы для работы с активностями пользователей.
    """
    
    def get_user_activities(self, user: 'User', activity_type: Optional[str] = None) -> QuerySet['UserActivity']:
        """
        Получает активности пользователя с фильтрацией по типу.
        
        Args:
            user: Пользователь, чьи активности нужно получить
            activity_type: Тип активности для фильтрации (опционально)
            
        Returns:
            QuerySet[UserActivity]: Queryset активностей пользователя
        """
        try:
            queryset = self.filter(user=user)
            
            if activity_type:
                queryset = queryset.filter(activity_type=activity_type)
                
            return queryset.select_related(
                'track', 
                'track__artist', 
                'track__album',
                'album',
                'album__artist',
                'artist'
            ).order_by('-timestamp')
        except Exception as e:
            print(f"Ошибка в get_user_activities: {str(e)}")
            return self.none()

    def get_liked_tracks(self, user: 'User') -> QuerySet['UserActivity']:
        """
        Получает лайкнутые треки пользователя.
        
        Args:
            user: Пользователь, чьи лайки нужно получить
            
        Returns:
            QuerySet[UserActivity]: Queryset лайков пользователя на треки
        """
        try:
            return self.get_user_activities(
                user=user,
                activity_type='like'
            ).filter(track__isnull=False)
        except Exception as e:
            print(f"Ошибка в get_liked_tracks: {str(e)}")
            return self.none()


class TrackManager(models.Manager):
    """
    Менеджер для модели Track.
    
    Предоставляет методы для работы с треками и получения статистики.
    """
    
    def get_tracks_with_related(self) -> QuerySet['Track']:
        """
        Получает треки со всеми связанными данными.
        
        Использует select_related и prefetch_related для оптимизации запросов.
        
        Returns:
            QuerySet[Track]: Queryset треков с предзагруженными связанными данными
        """
        return self.select_related(
            'artist',
            'album'
        ).prefetch_related(
            'genres',
            'user_activities'
        )
    
    def get_genre_statistics(self) -> QuerySet[Dict[str, Any]]:
        """
        Получает статистику по трекам для каждого жанра.
        
        Включает:
        - Количество треков
        - Общую длительность
        - Среднее количество прослушиваний
        - Среднее количество лайков
        
        Returns:
            QuerySet[Dict[str, Any]]: Статистика по жанрам
        """
        return self.values('genres__title').annotate(
            tracks_count=Count('id'),
            total_duration=Sum('duration'),
            avg_play_count=Avg('play_count'),
            avg_likes=Avg('likes_count')
        ).order_by('-tracks_count')

    def get_tracks_with_popularity(self) -> QuerySet[Dict[str, Any]]:
        """
        Аннотирует треки показателем популярности.
        
        Returns:
            QuerySet[Dict[str, Any]]: Треки с показателями популярности
        """
        return self.prefetch_related(
            'genres'
        ).values('genres__title').annotate(
            tracks_count=Count('id'),
            total_duration=Sum('duration'),
            avg_play_count=Avg('play_count'),
            avg_likes=Avg('likes_count')
        ).order_by('-tracks_count')

    def get_top_artists_by_duration(self, limit: int = 10) -> QuerySet[Dict[str, Any]]:
        """
        Получает топ исполнителей по общей длительности треков.
        
        Включает дополнительную статистику:
        - Общее количество треков
        - Средняя длительность трека
        - Общее количество прослушиваний
        
        Args:
            limit: Максимальное количество исполнителей для возврата
            
        Returns:
            QuerySet[Dict[str, Any]]: Топ исполнителей с статистикой
        """
        return self.values('artist__email').annotate(
            total_tracks=Count('id'),
            total_duration=Sum('duration'),
            avg_track_duration=ExpressionWrapper(
                Sum('duration') * 1.0 / Count('id'),
                output_field=FloatField()
            ),
            total_plays=Sum('play_count')
        ).order_by('-total_duration')[:limit]