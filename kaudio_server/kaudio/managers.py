from django.db import models
from django.utils import timezone
from django.db.models import Count, Sum, F, FloatField, ExpressionWrapper, Q, Avg

class UserActivityManager(models.Manager):
    def get_user_activities(self, user, activity_type=None):
        """
        Базовый метод для получения активностей пользователя
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

    def get_liked_tracks(self, user):
        """
        Получить лайкнутые треки пользователя
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
    def get_tracks_with_related(self):
        """Получить треки со всеми связанными данными"""
        return self.select_related(
            'artist',
            'album'
        ).prefetch_related(
            'genres',
            'user_activities'
        )
    
    def get_genre_statistics(self):
        """
        Получает статистику по трекам для каждого жанра:
        - Количество треков
        - Общая длительность
        - Среднее количество прослушиваний
        - Среднее количество лайков
        """
        return self.values('genres__title').annotate(
            tracks_count=Count('id'),
            total_duration=Sum('duration'),
            avg_play_count=Avg('play_count'),
            avg_likes=Avg('likes_count')
        ).order_by('-tracks_count')

    def get_tracks_with_popularity(self):
        """Аннотирует треки показателем популярности"""
        return self.prefetch_related(
            'genres'
        ).values('genres__title').annotate(
            tracks_count=Count('id'),
            total_duration=Sum('duration'),
            avg_play_count=Avg('play_count'),
            avg_likes=Avg('likes_count')
        ).order_by('-tracks_count')

    def get_top_artists_by_duration(self, limit=10):
        """
        Получает топ исполнителей по общей длительности треков
        с дополнительной статистикой:
        - Общее количество треков
        - Средняя длительность трека
        - Общее количество прослушиваний
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