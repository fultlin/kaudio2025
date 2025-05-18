from django.db import models
from django.utils import timezone

class UserActivityManager(models.Manager):
    def get_user_activities(self, user, activity_type=None):
        """
        Базовый метод для получения активностей пользователя
        """
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
        )

    def get_liked_tracks(self, user):
        """
        Получить лайкнутые треки пользователя
        """
        return self.get_user_activities(
            user=user,
            activity_type='like'
        ).filter(track__isnull=False)