from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Artist, Genre, Album, Track, Playlist, UserActivity,
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre
)


class AlbumGenreInline(admin.TabularInline):
    model = AlbumGenre
    extra = 1
    verbose_name = _('Жанр')
    verbose_name_plural = _('Жанры')
    raw_id_fields = ['genre']


class TrackGenreInline(admin.TabularInline):
    model = TrackGenre
    extra = 1
    verbose_name = _('Жанр')
    verbose_name_plural = _('Жанры')
    raw_id_fields = ['genre']


class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 1
    verbose_name = _('Трек')
    verbose_name_plural = _('Треки')
    raw_id_fields = ['track']


class TrackInline(admin.TabularInline):
    model = Track
    extra = 1
    verbose_name = _('Трек')
    verbose_name_plural = _('Треки')
    fields = ['title', 'track_number', 'duration']
    raw_id_fields = ['artist']


class UserAlbumInline(admin.TabularInline):
    model = UserAlbum
    extra = 1
    verbose_name = _('Альбом пользователя')
    verbose_name_plural = _('Альбомы пользователя')
    raw_id_fields = ['album']


class UserTrackInline(admin.TabularInline):
    model = UserTrack
    extra = 1
    verbose_name = _('Трек пользователя')
    verbose_name_plural = _('Треки пользователя')
    raw_id_fields = ['track']


class UserSubscribeInline(admin.TabularInline):
    model = UserSubscribe
    extra = 1
    verbose_name = _('Подписка пользователя')
    verbose_name_plural = _('Подписки пользователя')


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'role', 'get_last_login', 'is_active']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email']
    readonly_fields = ['last_login', 'date_joined']
    date_hierarchy = 'date_joined'
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('username', 'email', 'password')
        }),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'img_profile_url')
        }),
        (_('Разрешения'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'role')
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    inlines = [UserSubscribeInline, UserAlbumInline, UserTrackInline]
    
    @admin.display(description=_('Последний вход'), ordering='last_login')
    def get_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return _('Нет данных')


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_email', 'is_verified', 'monthly_listeners']
    list_filter = ['is_verified']
    search_fields = ['email', 'id']
    readonly_fields = ['monthly_listeners']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('email', 'img_cover_url', 'is_verified')
        }),
        (_('Дополнительно'), {
            'fields': ('bio', 'monthly_listeners')
        }),
    )
    inlines = [TrackInline]
    
    @admin.display(description=_('Email'), ordering='email')
    def get_email(self, obj):
        return obj.email or _('Не указан')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_tracks_count', 'get_albums_count']
    search_fields = ['title']
    
    @admin.display(description=_('Количество треков'))
    def get_tracks_count(self, obj):
        return obj.tracks.count()
    
    @admin.display(description=_('Количество альбомов'))
    def get_albums_count(self, obj):
        return obj.albums.count()


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_artist', 'release_date', 'total_tracks', 'total_duration_minutes']
    list_filter = ['release_date']
    search_fields = ['title', 'artist__email']
    date_hierarchy = 'release_date'
    raw_id_fields = ['artist']
    readonly_fields = ['total_tracks', 'total_duration']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title', 'artist', 'release_date', 'img_url')
        }),
        (_('Статистика'), {
            'fields': ('total_tracks', 'total_duration')
        }),
    )
    inlines = [AlbumGenreInline, TrackInline]
    
    @admin.display(description=_('Исполнитель'), ordering='artist__email')
    def get_artist(self, obj):
        return obj.artist.email if obj.artist.email else f'Исполнитель #{obj.artist.id}'
    
    @admin.display(description=_('Продолжительность (мин)'), ordering='total_duration')
    def total_duration_minutes(self, obj):
        minutes = obj.total_duration // 60
        seconds = obj.total_duration % 60
        return f'{minutes}:{seconds:02d}'


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_artist', 'get_album', 'duration_display', 'play_count', 'is_explicit']
    list_filter = ['is_explicit', 'release_date']
    search_fields = ['title', 'artist__email', 'album__title']
    date_hierarchy = 'release_date'
    raw_id_fields = ['artist', 'album']
    readonly_fields = ['play_count', 'likes_count']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title', 'artist', 'album', 'track_number', 'release_date')
        }),
        (_('Медиа'), {
            'fields': ('img_url', 'duration', 'is_explicit', 'lyrics')
        }),
        (_('Статистика'), {
            'fields': ('play_count', 'likes_count')
        }),
    )
    inlines = [TrackGenreInline]
    
    @admin.display(description=_('Исполнитель'), ordering='artist__email')
    def get_artist(self, obj):
        return obj.artist.email if obj.artist.email else f'Исполнитель #{obj.artist.id}'
    
    @admin.display(description=_('Альбом'), ordering='album__title')
    def get_album(self, obj):
        return obj.album.title
    
    @admin.display(description=_('Продолжительность'), ordering='duration')
    def duration_display(self, obj):
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f'{minutes}:{seconds:02d}'


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_user', 'creation_date', 'is_public', 'total_tracks', 'total_duration_minutes']
    list_filter = ['is_public', 'creation_date']
    search_fields = ['title', 'user__username']
    date_hierarchy = 'creation_date'
    raw_id_fields = ['user']
    readonly_fields = ['creation_date', 'total_tracks', 'total_duration']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title', 'user', 'img_url', 'is_public')
        }),
        (_('Статистика'), {
            'fields': ('creation_date', 'total_tracks', 'total_duration')
        }),
    )
    inlines = [PlaylistTrackInline]
    
    @admin.display(description=_('Пользователь'), ordering='user__username')
    def get_user(self, obj):
        return obj.user.username
    
    @admin.display(description=_('Продолжительность (мин)'), ordering='total_duration')
    def total_duration_minutes(self, obj):
        minutes = obj.total_duration // 60
        seconds = obj.total_duration % 60
        return f'{minutes}:{seconds:02d}'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'activity_type', 'get_related_item', 'timestamp', 'duration_display']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['user__username', 'track__title', 'playlist__title', 'artist__email']
    date_hierarchy = 'timestamp'
    raw_id_fields = ['user', 'track', 'playlist', 'artist']
    readonly_fields = ['timestamp']
    
    @admin.display(description=_('Пользователь'), ordering='user__username')
    def get_user(self, obj):
        return obj.user.username
    
    @admin.display(description=_('Объект активности'))
    def get_related_item(self, obj):
        if obj.track:
            return f'{_("Трек")}: {obj.track.title}'
        elif obj.playlist:
            return f'{_("Плейлист")}: {obj.playlist.title}'
        elif obj.artist:
            return f'{_("Исполнитель")} #{obj.artist.id}'
        return _('Не указан')
    
    @admin.display(description=_('Продолжительность'), ordering='duration')
    def duration_display(self, obj):
        if not obj.duration:
            return '-'
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f'{minutes}:{seconds:02d}'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ['get_type_display', 'get_users_count']
    search_fields = ['type']
    inlines = [UserSubscribeInline]
    
    @admin.display(description=_('Тип подписки'))
    def get_type_display(self, obj):
        return obj.get_type_display()
    
    @admin.display(description=_('Количество пользователей'))
    def get_users_count(self, obj):
        return obj.users.count()


@admin.register(UserSubscribe)
class UserSubscribeAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_subscribe_type', 'start_date', 'end_date']
    list_filter = ['subscribe__type', 'start_date', 'end_date']
    search_fields = ['user__username']
    date_hierarchy = 'start_date'
    raw_id_fields = ['user']
    
    @admin.display(description=_('Пользователь'), ordering='user__username')
    def get_user(self, obj):
        return obj.user.username
    
    @admin.display(description=_('Тип подписки'), ordering='subscribe__type')
    def get_subscribe_type(self, obj):
        return obj.subscribe.get_type_display()


@admin.register(UserAlbum)
class UserAlbumAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_album', 'position', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'album__title']
    date_hierarchy = 'added_at'
    raw_id_fields = ['user', 'album']
    
    @admin.display(description=_('Пользователь'), ordering='user__username')
    def get_user(self, obj):
        return obj.user.username
    
    @admin.display(description=_('Альбом'), ordering='album__title')
    def get_album(self, obj):
        return obj.album.title


@admin.register(UserTrack)
class UserTrackAdmin(admin.ModelAdmin):
    list_display = ['get_user', 'get_track', 'position', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'track__title']
    date_hierarchy = 'added_at'
    raw_id_fields = ['user', 'track']
    
    @admin.display(description=_('Пользователь'), ordering='user__username')
    def get_user(self, obj):
        return obj.user.username
    
    @admin.display(description=_('Трек'), ordering='track__title')
    def get_track(self, obj):
        return obj.track.title


@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    list_display = ['get_playlist', 'get_track', 'position', 'added_at']
    list_filter = ['added_at']
    search_fields = ['playlist__title', 'track__title']
    date_hierarchy = 'added_at'
    raw_id_fields = ['playlist', 'track']
    
    @admin.display(description=_('Плейлист'), ordering='playlist__title')
    def get_playlist(self, obj):
        return obj.playlist.title
    
    @admin.display(description=_('Трек'), ordering='track__title')
    def get_track(self, obj):
        return obj.track.title


@admin.register(AlbumGenre)
class AlbumGenreAdmin(admin.ModelAdmin):
    list_display = ['get_album', 'get_genre']
    search_fields = ['album__title', 'genre__title']
    raw_id_fields = ['album', 'genre']
    
    @admin.display(description=_('Альбом'), ordering='album__title')
    def get_album(self, obj):
        return obj.album.title
    
    @admin.display(description=_('Жанр'), ordering='genre__title')
    def get_genre(self, obj):
        return obj.genre.title


@admin.register(TrackGenre)
class TrackGenreAdmin(admin.ModelAdmin):
    list_display = ['get_track', 'get_genre']
    search_fields = ['track__title', 'genre__title']
    raw_id_fields = ['track', 'genre']
    
    @admin.display(description=_('Трек'), ordering='track__title')
    def get_track(self, obj):
        return obj.track.title
    
    @admin.display(description=_('Жанр'), ordering='genre__title')
    def get_genre(self, obj):
        return obj.genre.title
