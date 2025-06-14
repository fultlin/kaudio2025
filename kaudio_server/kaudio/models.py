import os
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.core.files.storage import default_storage
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg

from .managers import UserActivityManager, TrackManager

def get_artist_image_path(instance, filename):
    """Путь для сохранения изображений артиста"""
    return f'artist_images/{instance.id}/{filename}'

def get_album_image_path(instance, filename):
    """Путь для сохранения обложек альбомов"""
    return f'album_images/{instance.id}/{filename}'

def get_track_image_path(instance, filename):
    """Путь для сохранения обложек треков"""
    return f'track_images/{instance.id}/{filename}'

def get_profile_image_path(instance, filename):
    """Путь для сохранения изображений профиля"""
    return f'profile_images/{instance.id}/{filename}'

def get_playlist_image_path(instance, filename):
    """Путь для сохранения обложек плейлистов"""
    return f'playlist_images/{instance.id}/{filename}'

class User(AbstractUser):
    """Модель пользователя"""
    
    ROLE_CHOICES = (
        ('admin', _('Администратор')),
        ('user', _('Пользователь')),
        ('artist', _('Исполнитель')),
        ('moderator', _('Модератор')),
    )
    
    profile_image = models.ImageField(
        upload_to=get_profile_image_path,
        verbose_name='Изображение профиля',
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name=_('Роль')
    )
    
    @property
    def img_profile_url(self):
        if self.profile_image:
            return self.profile_image.url
        return None

    def save(self, *args, **kwargs):
        if self.img_profile_url and not self.profile_image:
            try:
                from urllib.request import urlopen
                from django.core.files import File
                from django.core.files.temp import NamedTemporaryFile

                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write(urlopen(self.img_profile_url).read())
                img_temp.flush()
                
                self.profile_image.save(
                    os.path.basename(self.img_profile_url),
                    File(img_temp)
                )
            except:
                pass
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['username']
    
    def __str__(self):
        return self.username


class Artist(models.Model):
    """Модель исполнителя"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='artist_profile',
        verbose_name=_('Пользователь'),
        null=True,
        blank=True
    )
    bio = models.TextField(
        verbose_name=_('Биография'),
        blank=True,
        null=True
    )
    email = models.EmailField(
        verbose_name=_('Email'),
        blank=True,
        null=True
    )
    cover_image = models.ImageField(
        upload_to=get_artist_image_path,
        verbose_name=_('Изображение обложки'),
        blank=True,
        null=True
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('Верифицирован')
    )
    monthly_listeners = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ежемесячных слушателей')
    )
    username = models.CharField(
        max_length=150,
        verbose_name=_('Имя пользователя'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Исполнитель')
        verbose_name_plural = _('Исполнители')
        ordering = ['id']
    
    def __str__(self):
        return f'Исполнитель #{self.id}'

    def save(self, *args, **kwargs):
        if self.user:
            self.username = self.user.username
        super().save(*args, **kwargs)


class Genre(models.Model):
    """Модель жанра музыки"""
    
    title = models.CharField(
        max_length=100,
        verbose_name=_('Название')
    )
    img_url = models.URLField(
        verbose_name=_('Ссылка на изображение'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Жанр')
        verbose_name_plural = _('Жанры')
        ordering = ['title']
    
    def __str__(self):
        return self.title


class Album(models.Model):
    """Модель альбома"""
    
    title = models.CharField(
        max_length=200, 
        verbose_name=_('Название')
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='albums',
        verbose_name=_('Исполнитель')
    )
    release_date = models.DateField(
        verbose_name=_('Дата выпуска')
    )
    cover_image = models.ImageField(
        upload_to=get_album_image_path,
        verbose_name=_('Изображение обложки'),
        blank=True,
        null=True
    )
    total_tracks = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Всего треков')
    )
    total_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Общая продолжительность (сек)')
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Количество лайков')
    )
    play_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Количество прослушиваний')
    )
    genres = models.ManyToManyField(
        Genre,
        through='AlbumGenre',
        related_name='albums',
        verbose_name=_('Жанры')
    )
    
    class Meta:
        verbose_name = _('Альбом')
        verbose_name_plural = _('Альбомы')
        ordering = ['-release_date']
    
    def __str__(self):
        return self.title


class Track(models.Model):
    """Модель трека"""
    
    title = models.CharField(
        max_length=255,
        verbose_name=_('Название')
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='tracks',
        verbose_name=_('Исполнитель')
    )
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='tracks',
        verbose_name=_('Альбом'),
        null=True,
        blank=True
    )
    audio_file = models.FileField(
        upload_to='tracks/',
        verbose_name=_('Аудиофайл'),
        null=True,
        blank=True
    )
    track_number = models.IntegerField(
        verbose_name=_('Номер трека'),
        null=True,
        blank=True
    )
    release_date = models.DateField(
        verbose_name=_('Дата выпуска'),
        null=True,
        blank=True
    )
    cover_image = models.ImageField(
        upload_to=get_track_image_path,
        verbose_name=_('Изображение обложки'),
        blank=True,
        null=True
    )
    duration = models.IntegerField(
        verbose_name=_('Продолжительность (сек)'),
        null=True,
        blank=True
    )
    play_count = models.IntegerField(
        default=0,
        verbose_name=_('Количество воспроизведений')
    )
    likes_count = models.IntegerField(
        default=0,
        verbose_name=_('Количество лайков')
    )
    is_explicit = models.BooleanField(
        default=False,
        verbose_name=_('Содержит ненормативную лексику')
    )
    lyrics = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Текст песни')
    )
    genres = models.ManyToManyField(
        Genre,
        through='TrackGenre',
        related_name='tracks',
        verbose_name=_('Жанры')
    )
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
        verbose_name=_('Средний рейтинг')
    )
    
    objects = TrackManager()
    
    class Meta:
        verbose_name = _('Трек')
        verbose_name_plural = _('Треки')
        ordering = ['album', 'track_number']
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'album'],
                name='unique_track_title_in_album',
                condition=models.Q(album__isnull=False)
            )
        ]
    
    def __str__(self):
        return f'{self.title} - {self.artist}'
    
    def clean(self):
        """Проверяет уникальность названия трека в альбоме"""
        from django.core.exceptions import ValidationError
        
        if self.album:
            # Проверяем, существует ли трек с таким же названием в альбоме
            existing_track = Track.objects.filter(
                album=self.album,
                title__iexact=self.title
            ).exclude(pk=self.pk).first()
            
            if existing_track:
                raise ValidationError({
                    'title': _('Трек с таким названием уже существует в этом альбоме')
                })


class Playlist(models.Model):
    """Модель плейлиста"""
    
    title = models.CharField(
        max_length=200,
        verbose_name=_('Название')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='playlists',
        verbose_name=_('Пользователь')
    )
    cover_image = models.ImageField(
        upload_to=get_playlist_image_path,
        verbose_name=_('Изображение обложки'),
        blank=True,
        null=True
    )
    creation_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Публичный')
    )
    total_tracks = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Всего треков')
    )
    total_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Общая продолжительность (сек)')
    )
    tracks = models.ManyToManyField(
        Track,
        through='PlaylistTrack',
        related_name='playlists',
        verbose_name=_('Треки')
    )
    
    class Meta:
        verbose_name = _('Плейлист')
        verbose_name_plural = _('Плейлисты')
        ordering = ['-creation_date']
    
    def __str__(self):
        return f'{self.title} ({self.user.username})'


class UserActivity(models.Model):
    """Модель активности пользователя"""
    
    ACTIVITY_TYPES = (
        ('play', _('Воспроизведение')),
        ('like', _('Лайк')),
        ('like_album', _('Лайк альбома')),
        ('add_to_playlist', _('Добавление в плейлист')),
        ('remove_from_playlist', _('Удаление из плейлиста')),
        ('follow_artist', _('Подписка на исполнителя')),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('Пользователь')
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
        verbose_name=_('Тип активности')
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.SET_NULL,
        related_name='user_activities',
        verbose_name=_('Трек'),
        null=True,
        blank=True
    )
    album = models.ForeignKey(
        Album,
        on_delete=models.SET_NULL,
        related_name='user_activities',
        verbose_name=_('Альбом'),
        null=True,
        blank=True
    )
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.SET_NULL,
        related_name='user_activities',
        verbose_name=_('Плейлист'),
        null=True,
        blank=True
    )
    artist = models.ForeignKey(
        Artist,
        on_delete=models.SET_NULL,
        related_name='user_activities',
        verbose_name=_('Исполнитель'),
        null=True,
        blank=True
    )
    duration = models.PositiveIntegerField(
        verbose_name=_('Продолжительность (сек)'),
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Время')
    )
    
    objects = UserActivityManager()
    
    class Meta:
        verbose_name = _('Активность пользователя')
        verbose_name_plural = _('Активности пользователей')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"
    
    def clean(self):
        """Проверяет, что для каждого типа активности указаны соответствующие поля"""
        from django.core.exceptions import ValidationError
        
        if self.activity_type == 'play':
            if not any([self.track, self.album]):
                raise ValidationError(_("Для активности 'play' необходимо указать трек или альбом"))
        elif self.activity_type == 'like':
            if not any([self.track, self.album, self.artist]):
                raise ValidationError(_("Для активности 'like' необходимо указать трек, альбом или исполнителя"))
        elif self.activity_type == 'follow_artist':
            if not self.artist:
                raise ValidationError(_("Для активности 'follow_artist' необходимо указать исполнителя"))
        elif self.activity_type in ['add_to_playlist', 'remove_from_playlist']:
            if not all([self.track, self.playlist]):
                raise ValidationError(_("Для активности 'add_to_playlist' или 'remove_from_playlist' необходимо указать трек и плейлист"))
    
    def save(self, *args, **kwargs):
        """Сохраняет активность и обновляет связанные счетчики"""
        self.full_clean()
        
        if self.activity_type == 'play':
            if self.track:
                self.track.play_count += 1
                self.track.save()
            if self.album:
                self.album.play_count = self.album.play_count + 1 if hasattr(self.album, 'play_count') else 1
                self.album.save()
        elif self.activity_type == 'like':
            if self.track:
                self.track.likes_count += 1
                self.track.save()
            elif self.album:
                self.album.likes_count += 1
                self.album.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Удаляет активность и обновляет связанные счетчики"""
        # Обновляем счетчики в зависимости от типа активности
        if self.activity_type == 'like':
            if self.track:
                self.track.likes_count = max(0, self.track.likes_count - 1)
                self.track.save()
            elif self.album:
                self.album.likes_count = max(0, self.album.likes_count - 1)
                self.album.save()
        
        super().delete(*args, **kwargs)


class Subscribe(models.Model):
    """Модель подписки"""
    
    SUBSCRIPTION_TYPES = (
        ('free', _('Бесплатная')),
        ('premium', _('Премиум')),
        ('family', _('Семейная')),
    )
    
    type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TYPES,
        verbose_name=_('Тип подписки')
    )
    permissions = models.TextField(
        verbose_name=_('Разрешения')
    )
    
    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
    
    def __str__(self):
        return self.get_type_display()


class UserSubscribe(models.Model):
    """Модель подписки пользователя"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribes',
        verbose_name=_('Пользователь')
    )
    subscribe = models.ForeignKey(
        Subscribe,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name=_('Подписка')
    )
    start_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Дата начала')
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Дата окончания')
    )
    
    class Meta:
        verbose_name = _('Подписка пользователя')
        verbose_name_plural = _('Подписки пользователей')
        unique_together = ['user', 'subscribe']
    
    def __str__(self):
        return f'{self.user.username} - {self.subscribe}'


class UserAlbum(models.Model):
    """Модель альбома пользователя"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_albums',
        verbose_name=_('Пользователь')
    )
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='user_albums',
        verbose_name=_('Альбом')
    )
    position = models.PositiveIntegerField(
        verbose_name=_('Позиция')
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Добавлен')
    )
    
    class Meta:
        verbose_name = _('Альбом пользователя')
        verbose_name_plural = _('Альбомы пользователей')
        unique_together = ['user', 'album']
        ordering = ['position']
    
    def __str__(self):
        return f'{self.user.username} - {self.album.title}'


class UserTrack(models.Model):
    """Модель трека пользователя"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_tracks',
        verbose_name=_('Пользователь')
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        related_name='user_tracks',
        verbose_name=_('Трек')
    )
    position = models.PositiveIntegerField(
        verbose_name=_('Позиция')
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Добавлен')
    )
    
    class Meta:
        verbose_name = _('Трек пользователя')
        verbose_name_plural = _('Треки пользователей')
        unique_together = ['user', 'track']
        ordering = ['position']
    
    def __str__(self):
        return f'{self.user.username} - {self.track.title}'


class PlaylistTrack(models.Model):
    """Модель связи плейлист-трек"""
    
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        verbose_name=_('Плейлист')
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        verbose_name=_('Трек')
    )
    position = models.PositiveIntegerField(
        verbose_name=_('Позиция')
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Добавлен')
    )
    
    class Meta:
        verbose_name = _('Трек в плейлисте')
        verbose_name_plural = _('Треки в плейлистах')
        unique_together = ['playlist', 'track']
        ordering = ['position']
    
    def __str__(self):
        return f'{self.playlist.title} - {self.track.title}'


class AlbumGenre(models.Model):
    """Модель связи альбом-жанр"""
    
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        verbose_name=_('Альбом')
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name=_('Жанр')
    )
    
    class Meta:
        verbose_name = _('Жанр альбома')
        verbose_name_plural = _('Жанры альбомов')
        unique_together = ['album', 'genre']
    
    def __str__(self):
        return f'{self.album.title} - {self.genre.title}'


class TrackGenre(models.Model):
    """Модель связи трек-жанр"""
    
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        verbose_name=_('Трек')
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name=_('Жанр')
    )
    
    class Meta:
        verbose_name = _('Жанр трека')
        verbose_name_plural = _('Жанры треков')
        unique_together = ['track', 'genre']
    
    def __str__(self):
        return f'{self.track.title} - {self.genre.title}'


class Statistics(models.Model):
    """Модель для статистики"""
    
    class Meta:
        verbose_name = _('Статистика')
        verbose_name_plural = _('Статистика')
        managed = False
        
    def get_absolute_url(self):
        """Возвращает URL для просмотра статистики"""
        return reverse('track-genre-statistics')
    
    @property
    def genre_statistics_url(self):
        """URL для статистики по жанрам"""
        return reverse('track-genre-statistics')
    
    @property
    def popular_tracks_url(self):
        """URL для популярных треков"""
        return reverse('track-popular-tracks')
    
    @property
    def top_artists_url(self):
        """URL для топ исполнителей"""
        return reverse('track-top-artists')


class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class TrackReview(Review):
    track = models.ForeignKey('Track', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='track_reviews')

    class Meta:
        unique_together = ('author', 'track')

class AlbumReview(Review):
    album = models.ForeignKey('Album', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='album_reviews')

    class Meta:
        unique_together = ('author', 'album')

@receiver([post_save, post_delete], sender=TrackReview)
def update_track_rating(sender, instance, **kwargs):
    """Обновляет средний рейтинг трека при изменении отзывов"""
    track = instance.track
    avg_rating = TrackReview.objects.filter(track=track).aggregate(
        avg=Avg('rating'))['avg']
    Track.objects.filter(id=track.id).update(avg_rating=avg_rating)
