import os
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

from kaudio_server.kaudio.managers import UserActivityManager

class User(AbstractUser):
    """Модель пользователя"""
    
    ROLE_CHOICES = (
        ('admin', _('Администратор')),
        ('user', _('Пользователь')),
        ('moderator', _('Модератор')),
    )
    
    img_profile_url = models.URLField(
        verbose_name=_('Ссылка на изображение профиля'),
        blank=True,
        null=True
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name=_('Роль')
    )
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['username']
    
    def __str__(self):
        return self.username


class Artist(models.Model):
    """Модель исполнителя"""
    
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
    img_cover_url = models.URLField(
        verbose_name=_('Ссылка на обложку'),
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
    
    class Meta:
        verbose_name = _('Исполнитель')
        verbose_name_plural = _('Исполнители')
        ordering = ['id']
    
    def __str__(self):
        return f'Исполнитель #{self.id}'


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
    img_url = models.URLField(
        verbose_name=_('Ссылка на обложку'),
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
        max_length=200,
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
    track_number = models.PositiveIntegerField(
        verbose_name=_('Номер трека'),
        null=True,
        blank=True
    )
    release_date = models.DateField(
        verbose_name=_('Дата выпуска'),
        null=True,
        blank=True
    )
    img_url = models.URLField(
        verbose_name=_('Ссылка на обложку'),
        blank=True,
        null=True
    )
    duration = models.PositiveIntegerField(
        verbose_name=_('Продолжительность (сек)')
    )
    play_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Количество воспроизведений')
    )
    likes_count = models.PositiveIntegerField(
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
    
    class Meta:
        verbose_name = _('Трек')
        verbose_name_plural = _('Треки')
        ordering = ['album', 'track_number']
    
    def __str__(self):
        return f'{self.title} - {self.artist}'


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
    img_url = models.URLField(
        verbose_name=_('Ссылка на обложку'),
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
    
    def __str__(self):
        return f'{self.user.username} - {self.get_activity_type_display()}'


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
