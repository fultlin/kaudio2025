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
from typing import Optional, Any, Dict, List, Union
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from urllib.request import urlopen

from .managers import UserActivityManager, TrackManager


def get_artist_image_path(instance: 'Artist', filename: str) -> str:
    """
    Генерирует путь для сохранения изображений артиста.
    
    Args:
        instance: Экземпляр модели Artist
        filename: Имя файла изображения
        
    Returns:
        str: Путь для сохранения файла
    """
    return f'artist_images/{instance.id}/{filename}'


def get_album_image_path(instance: 'Album', filename: str) -> str:
    """
    Генерирует путь для сохранения обложек альбомов.
    
    Args:
        instance: Экземпляр модели Album
        filename: Имя файла изображения
        
    Returns:
        str: Путь для сохранения файла
    """
    return f'album_images/{instance.id}/{filename}'


def get_track_image_path(instance: 'Track', filename: str) -> str:
    """
    Генерирует путь для сохранения обложек треков.
    
    Args:
        instance: Экземпляр модели Track
        filename: Имя файла изображения
        
    Returns:
        str: Путь для сохранения файла
    """
    return f'track_images/{instance.id}/{filename}'


def get_profile_image_path(instance: 'User', filename: str) -> str:
    """
    Генерирует путь для сохранения изображений профиля.
    
    Args:
        instance: Экземпляр модели User
        filename: Имя файла изображения
        
    Returns:
        str: Путь для сохранения файла
    """
    return f'profile_images/{instance.id}/{filename}'


def get_playlist_image_path(instance: 'Playlist', filename: str) -> str:
    """
    Генерирует путь для сохранения обложек плейлистов.
    
    Args:
        instance: Экземпляр модели Playlist
        filename: Имя файла изображения
        
    Returns:
        str: Путь для сохранения файла
    """
    return f'playlist_images/{instance.id}/{filename}'


class User(AbstractUser):
    """
    Расширенная модель пользователя с дополнительными полями.
    
    Добавляет поддержку ролей, изображения профиля и дополнительных функций.
    """
    
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
    def img_profile_url(self) -> Optional[str]:
        """
        Возвращает URL изображения профиля пользователя.
        
        Returns:
            Optional[str]: URL изображения или None, если изображение не установлено
        """
        if self.profile_image:
            return self.profile_image.url
        return None

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределенный метод сохранения с обработкой URL изображения.
        
        Если установлен img_profile_url, но нет profile_image, 
        пытается загрузить изображение по URL.
        
        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        """
        if self.img_profile_url and not self.profile_image:
            try:
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
    
    def __str__(self) -> str:
        """
        Строковое представление пользователя.
        
        Returns:
            str: Имя пользователя
        """
        return self.username


class Artist(models.Model):
    """
    Модель исполнителя.
    
    Представляет музыкального исполнителя с биографией, изображением
    и статистикой слушателей.
    """
    
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
    
    def __str__(self) -> str:
        """
        Строковое представление исполнителя.
        
        Returns:
            str: Идентификатор исполнителя
        """
        return f'Исполнитель #{self.id}'

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределенный метод сохранения.
        
        Автоматически устанавливает username из связанного пользователя.
        
        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        """
        if self.user:
            self.username = self.user.username
        super().save(*args, **kwargs)


class Genre(models.Model):
    """
    Модель жанра музыки.
    
    Представляет музыкальный жанр с названием и изображением.
    """
    
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
    
    def __str__(self) -> str:
        """
        Строковое представление жанра.
        
        Returns:
            str: Название жанра
        """
        return self.title


class Album(models.Model):
    """
    Модель альбома.
    
    Представляет музыкальный альбом с информацией о треках,
    продолжительности и статистике.
    """
    
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
    
    def __str__(self) -> str:
        """
        Строковое представление альбома.
        
        Returns:
            str: Название альбома
        """
        return self.title


class Track(models.Model):
    """
    Модель трека.
    
    Представляет отдельный музыкальный трек с аудиофайлом,
    метаданными и статистикой воспроизведений.
    """
    
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
                fields=['album', 'track_number'],
                name='unique_track_number_in_album'
            ),
            models.UniqueConstraint(
                fields=['album', 'title'],
                name='unique_track_title_in_album'
            )
        ]
    
    def __str__(self) -> str:
        """
        Строковое представление трека.
        
        Returns:
            str: Название трека
        """
        return self.title

    def clean(self) -> None:
        """
        Валидация модели трека.
        
        Проверяет корректность данных трека перед сохранением.
        
        Raises:
            ValidationError: Если данные некорректны
        """
        from django.core.exceptions import ValidationError
        
        if self.album and not self.track_number:
            raise ValidationError({
                'track_number': 'Номер трека обязателен для треков в альбоме'
            })
        
        if self.track_number and self.track_number < 1:
            raise ValidationError({
                'track_number': 'Номер трека должен быть положительным числом'
            })
        
        if self.duration and self.duration < 0:
            raise ValidationError({
                'duration': 'Продолжительность не может быть отрицательной'
            })


class Playlist(models.Model):
    """
    Модель плейлиста.
    
    Представляет пользовательский плейлист с треками,
    настройками приватности и статистикой.
    """
    
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
    
    def __str__(self) -> str:
        """
        Строковое представление плейлиста.
        
        Returns:
            str: Название плейлиста
        """
        return self.title


class UserActivity(models.Model):
    """
    Модель активности пользователя.
    
    Отслеживает различные действия пользователей: воспроизведения,
    лайки, добавления в плейлисты и подписки на исполнителей.
    """
    
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
            models.Index(fields=['track']),
            models.Index(fields=['album']),
        ]
    
    def __str__(self) -> str:
        """
        Строковое представление активности.
        
        Returns:
            str: Описание активности
        """
        return f'{self.user.username} - {self.get_activity_type_display()}'

    def clean(self) -> None:
        """
        Валидация модели активности.
        
        Проверяет корректность данных активности перед сохранением.
        
        Raises:
            ValidationError: Если данные некорректны
        """
        from django.core.exceptions import ValidationError
        
        # Проверяем, что указан хотя бы один связанный объект
        related_objects = [self.track, self.album, self.playlist, self.artist]
        if not any(related_objects):
            raise ValidationError(
                'Должен быть указан хотя бы один связанный объект (трек, альбом, плейлист или исполнитель)'
            )
        
        # Проверяем соответствие типа активности и связанного объекта
        if self.activity_type in ['play', 'like'] and not self.track:
            raise ValidationError({
                'track': 'Для данного типа активности должен быть указан трек'
            })
        
        if self.activity_type == 'like_album' and not self.album:
            raise ValidationError({
                'album': 'Для лайка альбома должен быть указан альбом'
            })
        
        if self.activity_type in ['add_to_playlist', 'remove_from_playlist'] and not self.playlist:
            raise ValidationError({
                'playlist': 'Для операций с плейлистом должен быть указан плейлист'
            })
        
        if self.activity_type == 'follow_artist' and not self.artist:
            raise ValidationError({
                'artist': 'Для подписки на исполнителя должен быть указан исполнитель'
            })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределенный метод сохранения.
        
        Обновляет статистику связанных объектов при сохранении активности.
        
        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
        """
        if self.activity_type == 'play' and self.track:
            self.track.play_count += 1
            self.track.save(update_fields=['play_count'])
        
        elif self.activity_type == 'like' and self.track:
            self.track.likes_count += 1
            self.track.save(update_fields=['likes_count'])
        
        elif self.activity_type == 'like_album' and self.album:
            self.album.likes_count += 1
            self.album.save(update_fields=['likes_count'])
        
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, Dict[str, int]]:
        """
        Переопределенный метод удаления.
        
        Обновляет статистику связанных объектов при удалении активности.
        
        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            tuple[int, Dict[str, int]]: Результат удаления
        """
        if self.activity_type == 'play' and self.track:
            self.track.play_count = max(0, self.track.play_count - 1)
            self.track.save(update_fields=['play_count'])
        
        elif self.activity_type == 'like' and self.track:
            self.track.likes_count = max(0, self.track.likes_count - 1)
            self.track.save(update_fields=['likes_count'])
        
        elif self.activity_type == 'like_album' and self.album:
            self.album.likes_count = max(0, self.album.likes_count - 1)
            self.album.save(update_fields=['likes_count'])
        
        return super().delete(*args, **kwargs)


class Subscribe(models.Model):
    """
    Модель подписки.
    
    Определяет типы подписок с их правами и ограничениями.
    """
    
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
        verbose_name=_('Права и ограничения'),
        blank=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Цена')
    )
    
    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
    
    def __str__(self) -> str:
        """
        Строковое представление подписки.
        
        Returns:
            str: Тип подписки
        """
        return self.get_type_display()


class UserSubscribe(models.Model):
    """
    Модель подписки пользователя.
    
    Связывает пользователей с их подписками и отслеживает период действия.
    """
    
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
        verbose_name=_('Дата окончания'),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )
    
    class Meta:
        verbose_name = _('Подписка пользователя')
        verbose_name_plural = _('Подписки пользователей')
        unique_together = ['user', 'subscribe']
    
    def __str__(self) -> str:
        """
        Строковое представление подписки пользователя.
        
        Returns:
            str: Описание подписки пользователя
        """
        return f'{self.user.username} - {self.subscribe.get_type_display()}'


class UserAlbum(models.Model):
    """
    Модель альбома пользователя.
    
    Связывает пользователей с альбомами в их библиотеке.
    """
    
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
        verbose_name=_('Дата добавления')
    )
    
    class Meta:
        verbose_name = _('Альбом пользователя')
        verbose_name_plural = _('Альбомы пользователей')
        unique_together = ['user', 'album']
        ordering = ['position']
    
    def __str__(self) -> str:
        """
        Строковое представление альбома пользователя.
        
        Returns:
            str: Описание альбома пользователя
        """
        return f'{self.user.username} - {self.album.title}'


class UserTrack(models.Model):
    """
    Модель трека пользователя.
    
    Связывает пользователей с треками в их библиотеке.
    """
    
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
        verbose_name=_('Дата добавления')
    )
    
    class Meta:
        verbose_name = _('Трек пользователя')
        verbose_name_plural = _('Треки пользователей')
        unique_together = ['user', 'track']
        ordering = ['position']
    
    def __str__(self) -> str:
        """
        Строковое представление трека пользователя.
        
        Returns:
            str: Описание трека пользователя
        """
        return f'{self.user.username} - {self.track.title}'


class PlaylistTrack(models.Model):
    """
    Модель связи плейлист-трек.
    
    Связывает треки с плейлистами и определяет их порядок.
    """
    
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
        verbose_name=_('Дата добавления')
    )
    
    class Meta:
        verbose_name = _('Трек в плейлисте')
        verbose_name_plural = _('Треки в плейлистах')
        unique_together = ['playlist', 'track']
        ordering = ['position']
    
    def __str__(self) -> str:
        """
        Строковое представление трека в плейлисте.
        
        Returns:
            str: Описание трека в плейлисте
        """
        return f'{self.playlist.title} - {self.track.title}'


class AlbumGenre(models.Model):
    """
    Модель связи альбом-жанр.
    
    Связывает альбомы с жанрами.
    """
    
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
    
    def __str__(self) -> str:
        """
        Строковое представление жанра альбома.
        
        Returns:
            str: Описание жанра альбома
        """
        return f'{self.album.title} - {self.genre.title}'


class TrackGenre(models.Model):
    """
    Модель связи трек-жанр.
    
    Связывает треки с жанрами.
    """
    
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
    
    def __str__(self) -> str:
        """
        Строковое представление жанра трека.
        
        Returns:
            str: Описание жанра трека
        """
        return f'{self.track.title} - {self.genre.title}'


class Statistics(models.Model):
    """
    Модель статистики.
    
    Предоставляет статистическую информацию о системе.
    """
    
    class Meta:
        verbose_name = _('Статистика')
        verbose_name_plural = _('Статистика')
        managed = False
    
    def get_absolute_url(self) -> str:
        """
        Возвращает абсолютный URL для статистики.
        
        Returns:
            str: URL статистики
        """
        return reverse('statistics')
    
    @property
    def genre_statistics_url(self) -> str:
        """
        URL для статистики по жанрам.
        
        Returns:
            str: URL статистики жанров
        """
        return reverse('genre_statistics')
    
    @property
    def popular_tracks_url(self) -> str:
        """
        URL для популярных треков.
        
        Returns:
            str: URL популярных треков
        """
        return reverse('popular_tracks')
    
    @property
    def top_artists_url(self) -> str:
        """
        URL для топ исполнителей.
        
        Returns:
            str: URL топ исполнителей
        """
        return reverse('top_artists')


class Review(models.Model):
    """
    Абстрактная модель отзыва.
    
    Базовый класс для отзывов на треки и альбомы.
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class TrackReview(Review):
    """
    Модель отзыва на трек.
    
    Позволяет пользователям оставлять отзывы на отдельные треки.
    """
    track = models.ForeignKey('Track', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='track_reviews')
    
    class Meta:
        unique_together = ('author', 'track')


class AlbumReview(Review):
    """
    Модель отзыва на альбом.
    
    Позволяет пользователям оставлять отзывы на альбомы.
    """
    album = models.ForeignKey('Album', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='album_reviews')
    
    class Meta:
        unique_together = ('author', 'album')


@receiver([post_save, post_delete], sender=TrackReview)
def update_track_rating(sender: Any, instance: TrackReview, **kwargs: Any) -> None:
    """
    Сигнал для обновления среднего рейтинга трека.
    
    Вызывается при сохранении или удалении отзыва на трек.
    
    Args:
        sender: Отправитель сигнала
        instance: Экземпляр отзыва
        **kwargs: Дополнительные аргументы
    """
    track = instance.track
    avg_rating = track.reviews.aggregate(avg=Avg('rating'))['avg']
    track.avg_rating = avg_rating
    track.save(update_fields=['avg_rating'])
