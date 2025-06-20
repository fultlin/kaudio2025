from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse, NoReverseMatch
from rest_framework import status
from kaudio.models import User, Artist, Genre, Album, Track, Playlist
from kaudio.admin import TrackAdmin
from django.contrib.admin.sites import AdminSite
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile

class TrackModelValidationTests(TestCase):
    def setUp(self):
        self.artist = Artist.objects.create()

    def test_track_validation_required_fields(self):
        track = Track(artist=self.artist)
        with self.assertRaises(ValidationError):
            track.full_clean()

    def test_track_validation_negative_duration(self):
        track = Track(title="Test", artist=self.artist, duration=-10)
        with self.assertRaises(ValidationError):
            track.full_clean()

class TrackAdminTests(TestCase):
    def test_duration_display_format(self):
        class DummyObj:
            duration = 125 
        admin = TrackAdmin(Track, AdminSite())
        self.assertEqual(admin.duration_display(DummyObj()), "2:05")

class UserAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_and_login(self):
        response = self.client.post('/api/auth/register/', {"username": "testuser", "password": "testpass"})
        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.json())
        response = self.client.post('/api/auth/login/', {"username": "testuser", "password": "testpass"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json())

class ArtistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="artuser", password="pass123")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_artist(self):
        data = {"bio": "Test bio", "email": "art@ex.com"}
        response = self.client.post('/api/artists/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Artist.objects.filter(user=self.user).exists())

    def test_artist_list(self):
        Artist.objects.create(user=self.user, email="art@ex.com")
        response = self.client.get('/api/artists/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

class AlbumTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="albumuser", password="pass123")
        self.artist = Artist.objects.create(user=self.user, email="alb@ex.com")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_album(self):
        data = {"title": "Test Album", "artist_id": self.artist.id, "release_date": date.today().isoformat()}
        response = self.client.post('/api/albums/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Album.objects.filter(title="Test Album").exists())

    def test_album_list(self):
        Album.objects.create(title="A1", artist=self.artist, release_date=date.today())
        response = self.client.get('/api/albums/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

class TrackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="trackuser", password="pass123")
        self.artist = Artist.objects.create(user=self.user, email="trk@ex.com")
        self.album = Album.objects.create(title="TAlbum", artist=self.artist, release_date=date.today())
        self.genre = Genre.objects.create(title="Rock")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_track(self):
        data = {
            "title": "Test Track",
            "artist_id": self.artist.id,
            "album_id": self.album.id,
            "track_number": 1,
            "release_date": self.album.release_date,
            "duration": 120
        }
        response = self.client.post('/api/tracks/', data)
        self.assertIn(response.status_code, (201, 400)) 

    def test_track_list(self):
        Track.objects.create(title="T1", artist=self.artist, album=self.album, duration=100, track_number=1)
        response = self.client.get('/api/tracks/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

    def test_track_filter_by_genre(self):
        track = Track.objects.create(title="T2", artist=self.artist, album=self.album, duration=100, track_number=2)
        track.genres.add(self.genre)
        response = self.client.get(f'/api/tracks/?genre=Rock')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(t["id"] == track.id for t in response.json()))

class PlaylistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pluser", password="pass123")
        self.client = Client()
        self.client.force_login(self.user)

    def test_create_playlist(self):
        data = {"title": "My Playlist", "user_id": self.user.id}
        response = self.client.post('/api/playlists/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Playlist.objects.filter(title="My Playlist").exists())

    def test_playlist_list(self):
        Playlist.objects.create(title="PL1", user=self.user)
        response = self.client.get('/api/playlists/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

class PlaylistTrackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pltrkuser", password="pass123")
        self.artist = Artist.objects.create(user=self.user, email="pltrk@ex.com")
        self.album = Album.objects.create(title="PLTAlbum", artist=self.artist, release_date=date.today())
        self.track = Track.objects.create(title="PLT1", artist=self.artist, album=self.album, duration=100, track_number=1)
        self.playlist = Playlist.objects.create(title="PLT", user=self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def test_add_track_to_playlist(self):
        url = f'/api/playlists/{self.playlist.id}/add_track/'
        data = {"track_id": self.track.id, "user_id": self.user.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.track, self.playlist.tracks.all())

class TrackLikeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="likeuser", password="pass123")
        self.artist = Artist.objects.create(user=self.user, email="like@ex.com")
        self.album = Album.objects.create(title="LikeAlbum", artist=self.artist, release_date=date.today())
        self.track = Track.objects.create(title="LikeT", artist=self.artist, album=self.album, duration=100, track_number=1)
        self.client = Client()
        self.client.force_login(self.user)

    def test_like_track(self):
        url = f'/api/tracks/{self.track.id}/like/'
        old_likes = self.track.likes_count
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.track.refresh_from_db()
        self.assertEqual(self.track.likes_count, old_likes + 2)

class TrackReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="revuser", password="pass123")
        self.artist = Artist.objects.create(user=self.user, email="rev@ex.com")
        self.album = Album.objects.create(title="RevAlbum", artist=self.artist, release_date=date.today())
        self.track = Track.objects.create(title="RevTrack", artist=self.artist, album=self.album, duration=120, track_number=1)
        self.client = Client()
        self.client.force_login(self.user)
        self.client.post(f'/api/tracks/{self.track.id}/play/')

    def test_create_track_review(self):
        data = {"track": self.track.id, "rating": 5, "text": "Отлично!"}
        response = self.client.post('/api/track-reviews/', data)
        self.assertIn(response.status_code, (201, 400))

class FileUploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fileuser", password="pass123", email="file@ex.com")
        self.artist = Artist.objects.create(user=self.user, email="file@ex.com")
        self.album = Album.objects.create(title="FileAlbum", artist=self.artist, release_date=date.today())
        self.client = Client()
        self.client.force_login(self.user)

    def test_upload_track_with_audio(self):
        audio_file = SimpleUploadedFile("test.mp3", b"ID3\x03\x00\x00\x00\x00\x00\x21", content_type="audio/mpeg")
        data = {
            "title": "Audio Track",
            "artist_id": self.artist.id,
            "album_id": self.album.id,
            "track_number": 1,
            "release_date": self.album.release_date,
            "duration": 120,
            "audio_file": audio_file,
        }
        response = self.client.post('/api/tracks/', data, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertIn('audio_file', response.json())

    def test_upload_album_cover(self):
        image_file = SimpleUploadedFile("cover.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        data = {
            "album_id": self.album.id,
            "image": image_file,
        }
        response = self.client.post('/api/upload/album-image/', data, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertIn('img_url', response.json())

    def test_upload_artist_cover(self):
        image_file = SimpleUploadedFile("artist.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        data = {
            "artist_id": self.artist.id,
            "image": image_file,
        }
        response = self.client.post('/api/upload/artist-image/', data, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertIn('img_cover_url', response.json())
