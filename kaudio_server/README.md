# Kaudio Server

Бэкенд музыкального стриминг-сервиса Kaudio.

## Установка

1. Клонировать репозиторий:

```
git clone <repository_url>
cd kaudio_server
```

2. Создать виртуальное окружение и активировать его:

```
python -m venv venv
# Для Windows
venv\Scripts\activate
# Для Linux/MacOS
source venv/bin/activate
```

3. Установить зависимости:

```
pip install -r requirements.txt
```

4. Применить миграции:

```
python manage.py migrate
```

5. Создать суперпользователя (необязательно):

```
python manage.py createsuperuser
```

6. Запустить сервер разработки:

```
python manage.py runserver
```

## API Endpoints

- `/api/users/` - пользователи
- `/api/artists/` - исполнители
- `/api/genres/` - жанры
- `/api/albums/` - альбомы
- `/api/tracks/` - треки
- `/api/playlists/` - плейлисты
- `/api/user-activities/` - активности пользователей
- `/api/subscribes/` - типы подписок
- `/api/user-subscribes/` - подписки пользователей
- `/api/user-albums/` - альбомы пользователей
- `/api/user-tracks/` - треки пользователей
- `/api/playlist-tracks/` - треки в плейлистах
- `/api/album-genres/` - жанры альбомов
- `/api/track-genres/` - жанры треков

## Дополнительные API действия

### Пользователи

- `/api/users/{id}/playlists/` - плейлисты пользователя
- `/api/users/{id}/activities/` - активности пользователя
- `/api/users/{id}/subscribes/` - подписки пользователя
- `/api/users/{id}/albums/` - альбомы пользователя
- `/api/users/{id}/tracks/` - треки пользователя

### Исполнители

- `/api/artists/{id}/albums/` - альбомы исполнителя
- `/api/artists/{id}/tracks/` - треки исполнителя

### Жанры

- `/api/genres/{id}/albums/` - альбомы определенного жанра
- `/api/genres/{id}/tracks/` - треки определенного жанра

### Альбомы

- `/api/albums/{id}/tracks/` - треки альбома
- `/api/albums/{id}/genres/` - жанры альбома

### Треки

- `/api/tracks/{id}/play/` - отметить воспроизведение трека
- `/api/tracks/{id}/like/` - поставить лайк треку
- `/api/tracks/{id}/genres/` - жанры трека

### Плейлисты

- `/api/playlists/{id}/tracks/` - треки плейлиста
- `/api/playlists/{id}/add_track/` - добавить трек в плейлист
- `/api/playlists/{id}/remove_track/` - удалить трек из плейлиста
