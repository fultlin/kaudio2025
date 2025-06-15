import django_filters
from .models import Track, Album, Artist, Playlist, UserActivity

class TrackFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    artist = django_filters.CharFilter(field_name='artist__user__username', lookup_expr='icontains')
    album = django_filters.CharFilter(field_name='album__title', lookup_expr='icontains')
    genre = django_filters.CharFilter(field_name='genres__title', lookup_expr='icontains')
    year = django_filters.NumberFilter(field_name='release_date__year')
    min_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='lte')
    is_explicit = django_filters.BooleanFilter()
    min_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='avg_rating', lookup_expr='lte')

    class Meta:
        model = Track
        fields = ['title', 'artist', 'album', 'genre', 'year', 'is_explicit']

class AlbumFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    artist = django_filters.CharFilter(field_name='artist__user__username', lookup_expr='icontains')
    genre = django_filters.CharFilter(field_name='genres__title', lookup_expr='icontains')
    year = django_filters.NumberFilter(field_name='release_date__year')
    min_tracks = django_filters.NumberFilter(field_name='total_tracks', lookup_expr='gte')
    max_tracks = django_filters.NumberFilter(field_name='total_tracks', lookup_expr='lte')
    min_duration = django_filters.NumberFilter(field_name='total_duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='total_duration', lookup_expr='lte')

    class Meta:
        model = Album
        fields = ['title', 'artist', 'genre', 'year']

class ArtistFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    bio = django_filters.CharFilter(lookup_expr='icontains')
    is_verified = django_filters.BooleanFilter()
    min_listeners = django_filters.NumberFilter(field_name='monthly_listeners', lookup_expr='gte')
    max_listeners = django_filters.NumberFilter(field_name='monthly_listeners', lookup_expr='lte')

    class Meta:
        model = Artist
        fields = ['username', 'email', 'is_verified']

class PlaylistFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    user = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    is_public = django_filters.BooleanFilter()
    min_tracks = django_filters.NumberFilter(field_name='total_tracks', lookup_expr='gte')
    max_tracks = django_filters.NumberFilter(field_name='total_tracks', lookup_expr='lte')
    min_duration = django_filters.NumberFilter(field_name='total_duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='total_duration', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='creation_date', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='creation_date', lookup_expr='lte')

    class Meta:
        model = Playlist
        fields = ['title', 'user', 'is_public']

class UserActivityFilter(django_filters.FilterSet):
    user = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    activity_type = django_filters.ChoiceFilter(choices=UserActivity.ACTIVITY_TYPES)
    track = django_filters.CharFilter(field_name='track__title', lookup_expr='icontains')
    album = django_filters.CharFilter(field_name='album__title', lookup_expr='icontains')
    artist = django_filters.CharFilter(field_name='artist__user__username', lookup_expr='icontains')
    min_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='lte')
    after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = UserActivity
        fields = ['user', 'activity_type', 'track', 'album', 'artist'] 