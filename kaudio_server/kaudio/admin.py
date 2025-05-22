from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Artist, Genre, Album, Track, Playlist, UserActivity,
    Subscribe, UserSubscribe, UserAlbum, UserTrack, PlaylistTrack,
    AlbumGenre, TrackGenre
)
from django.http import HttpResponse
from django.utils import timezone
from .utils.pdf_generator import generate_track_pdf, generate_album_pdf


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
            'fields': ('first_name', 'last_name', 'profile_image')
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
            'fields': ('email', 'cover_image', 'is_verified')
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
            'fields': ('title', 'artist', 'release_date', 'cover_image')
        }),
        (_('Статистика'), {
            'fields': ('total_tracks', 'total_duration')
        }),
    )
    inlines = [AlbumGenreInline, TrackInline]
    actions = ['export_as_pdf', 'recalculate_duration', 'mark_as_released']
    
    @admin.display(description=_('Исполнитель'), ordering='artist__email')
    def get_artist(self, obj):
        return obj.artist.email if obj.artist.email else f'Исполнитель #{obj.artist.id}'
    
    @admin.display(description=_('Продолжительность (мин)'), ordering='total_duration')
    def total_duration_minutes(self, obj):
        minutes = obj.total_duration // 60
        seconds = obj.total_duration % 60
        return f'{minutes}:{seconds:02d}'

    def recalculate_duration(self, request, queryset):
        """Пересчитывает общую длительность альбомов"""
        for album in queryset:
            total_duration = sum(track.duration for track in album.tracks.all())
            total_tracks = album.tracks.count()
            Album.objects.filter(id=album.id).update(
                total_duration=total_duration,
                total_tracks=total_tracks
            )
        self.message_user(request, _(
            f'Длительность пересчитана для {queryset.count()} альбомов'
        ))
    recalculate_duration.short_description = _("Пересчитать длительность")

    def mark_as_released(self, request, queryset):
        """Отмечает альбомы как выпущенные сегодня"""
        updated = queryset.update(release_date=timezone.now().date())
        self.message_user(request, _(
            f'{updated} альбомов отмечены как выпущенные сегодня'
        ))
    mark_as_released.short_description = _("Отметить как выпущенные сегодня")

    def export_as_pdf(self, request, queryset):
        """Экспортирует выбранные альбомы в PDF"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="albums_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        generate_album_pdf(queryset, response)
        return response
    export_as_pdf.short_description = _("Экспорт выбранных альбомов в PDF")


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_artist', 'get_album', 'duration_display', 'play_count', 'is_explicit']
    list_filter = ['is_explicit', 'release_date']
    search_fields = ['title', 'artist__email', 'album__title']
    date_hierarchy = 'release_date'
    raw_id_fields = ['artist', 'album']
    readonly_fields = ['play_count', 'likes_count', 'get_popularity_score']
    actions = ['export_as_pdf', 'reset_play_count', 'mark_as_explicit', 'mark_as_non_explicit']
    
    def get_popularity_score(self, obj):
        """Показывает рейтинг популярности трека"""
        tracks = Track.objects.get_tracks_with_popularity().filter(id=obj.id)
        if tracks:
            return f"{tracks[0].popularity_score:.2f}"
        return "0.00"
    get_popularity_score.short_description = _('Рейтинг популярности')

    def changelist_view(self, request, extra_context=None):
        """Добавляет статистику на страницу списка треков"""
        extra_context = extra_context or {}
        
        # Получаем статистику по жанрам
        genre_stats = Track.objects.get_genre_statistics()
        
        # Получаем топ-5 исполнителей
        top_artists = Track.objects.get_top_artists_by_duration(limit=5)
        
        extra_context['genre_statistics'] = genre_stats
        extra_context['top_artists'] = top_artists
        
        return super().changelist_view(request, extra_context=extra_context)
    
    @admin.display(description=_('Исполнитель'), ordering='artist__email')
    def get_artist(self, obj):
        return obj.artist.email if obj.artist.email else f'Исполнитель #{obj.artist.id}'
    
    @admin.display(description=_('Альбом'), ordering='album__title')
    def get_album(self, obj):
        if obj.album:
            return obj.album.title
        return _('Нет альбома')
    
    @admin.display(description=_('Продолжительность'), ordering='duration')
    def duration_display(self, obj):
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f'{minutes}:{seconds:02d}'

    def reset_play_count(self, request, queryset):
        """Сбрасывает счетчик прослушиваний для выбранных треков"""
        updated = queryset.update(play_count=0)
        self.message_user(request, _(
            f'Счетчик прослушиваний сброшен для {updated} треков'
        ))
    reset_play_count.short_description = _("Сбросить счетчик прослушиваний")

    def mark_as_explicit(self, request, queryset):
        """Отмечает выбранные треки как имеющие ненормативное содержание"""
        updated = queryset.update(is_explicit=True)
        self.message_user(request, _(
            f'{updated} треков отмечены как имеющие ненормативное содержание'
        ))
    mark_as_explicit.short_description = _("Отметить как 18+")

    def mark_as_non_explicit(self, request, queryset):
        """Отмечает выбранные треки как не имеющие ненормативного содержания"""
        updated = queryset.update(is_explicit=False)
        self.message_user(request, _(
            f'{updated} треков отмечены как не имеющие ненормативного содержания'
        ))
    mark_as_non_explicit.short_description = _("Снять отметку 18+")

    def export_as_pdf(self, request, queryset):
        """Экспортирует выбранные треки в PDF"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="tracks_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        generate_track_pdf(queryset, response)
        return response
    export_as_pdf.short_description = _("Экспорт выбранных треков в PDF")


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
            'fields': ('title', 'user', 'cover_image', 'is_public')
        }),
        (_('Статистика'), {
            'fields': ('creation_date', 'total_tracks', 'total_duration')
        }),
    )
    inlines = [PlaylistTrackInline]
    actions = ['make_public', 'make_private', 'recalculate_tracks']
    
    @admin.display(description=_('Пользователь'), ordering='user__username')
    def get_user(self, obj):
        return obj.user.username
    
    @admin.display(description=_('Продолжительность (мин)'), ordering='total_duration')
    def total_duration_minutes(self, obj):
        minutes = obj.total_duration // 60
        seconds = obj.total_duration % 60
        return f'{minutes}:{seconds:02d}'

    def make_public(self, request, queryset):
        """Делает выбранные плейлисты публичными"""
        updated = queryset.update(is_public=True)
        self.message_user(request, _(
            f'{updated} плейлистов стали публичными'
        ))
    make_public.short_description = _("Сделать публичными")

    def make_private(self, request, queryset):
        """Делает выбранные плейлисты приватными"""
        updated = queryset.update(is_public=False)
        self.message_user(request, _(
            f'{updated} плейлистов стали приватными'
        ))
    make_private.short_description = _("Сделать приватными")

    def recalculate_tracks(self, request, queryset):
        """Пересчитывает количество треков и общую длительность плейлистов"""
        for playlist in queryset:
            total_duration = sum(pt.track.duration for pt in playlist.playlist_tracks.all())
            total_tracks = playlist.playlist_tracks.count()
            Playlist.objects.filter(id=playlist.id).update(
                total_duration=total_duration,
                total_tracks=total_tracks
            )
        self.message_user(request, _(
            f'Статистика пересчитана для {queryset.count()} плейлистов'
        ))
    recalculate_tracks.short_description = _("Пересчитать статистику")


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
