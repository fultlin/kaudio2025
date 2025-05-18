import { makeAutoObservable, action } from "mobx";
import instance from "axiosurl/axios";
import { getFullImageUrl } from "../utils/imageUtils";
import { toJS } from "mobx";

class HomeStore {
  music = [];
  recentTracks = [];
  recentAlbums = [];
  likedTracks = [];
  likedAlbums = [];
  isLoading = false;
  error = null;
  // Кэш пользователей для сопоставления с артистами
  userCache = {};

  constructor() {
    makeAutoObservable(this, {
      setMusic: action,
      getTracks: action,
      setRecentTracks: action,
      setRecentAlbums: action,
      fetchRecentData: action,
      fetchLikedTracks: action,
      fetchLikedAlbums: action,
      likeTrack: action,
      unlikeTrack: action,
      likeAlbum: action,
      unlikeAlbum: action,
      setLikedTracks: action,
      setLikedAlbums: action,
      setLoading: action,
      setError: action,
      fetchArtistUser: action,
      fetchAlbumById: action,
      fetchAlbumTracks: action,
      isTrackLiked: action,
      isAlbumLiked: action,
    });
  }

  setMusic(tracks) {
    this.music = tracks.traks || [];
  }

  async getTracks(track) {
    try {
      const response = await instance.get(`music/${track}`);
      this.setMusic(response.data);
    } catch (error) {
      console.error("Ошибка при получении треков:", error);
      throw error;
    }
  }

  // Функция для получения пользователя, связанного с артистом
  async fetchArtistUser(artistEmail) {
    if (!artistEmail) return null;

    // Проверяем кэш
    if (this.userCache[artistEmail]) {
      return this.userCache[artistEmail];
    }

    try {
      // Получаем пользователей по email
      const response = await instance.get(
        `users/?search=${encodeURIComponent(artistEmail)}`
      );
      if (response.data && response.data.length > 0) {
        // Нашли пользователя
        const user = response.data[0];
        // Сохраняем в кэш
        this.userCache[artistEmail] = user;
        return user;
      }
      return null;
    } catch (error) {
      console.error("Ошибка при получении пользователя:", error);
      return null;
    }
  }

  async setRecentTracks(tracks) {
    // Преобразуем все URL изображений в треках
    const processedTracks = [];

    for (const track of tracks) {
      let artist = track.artist;

      if (artist && artist.email) {
        // Получаем пользователя для артиста
        const user = await this.fetchArtistUser(artist.email);

        // Добавляем информацию о пользователе к артисту
        artist = {
          ...artist,
          img_cover_url: artist.img_cover_url
            ? getFullImageUrl(artist.img_cover_url)
            : null,
          user: user,
        };
      }

      processedTracks.push({
        ...track,
        img_url: track.img_url ? getFullImageUrl(track.img_url) : null,
        artist: artist,
      });
    }

    this.recentTracks = processedTracks;
  }

  async setLikedTracks(tracks) {
    // Преобразуем все URL изображений в треках, аналогично setRecentTracks
    const processedTracks = [];

    for (const track of tracks) {
      let artist = track.artist;

      if (artist && artist.email) {
        // Получаем пользователя для артиста
        const user = await this.fetchArtistUser(artist.email);

        // Добавляем информацию о пользователе к артисту
        artist = {
          ...artist,
          img_cover_url: artist.img_cover_url
            ? getFullImageUrl(artist.img_cover_url)
            : null,
          user: user,
        };
      }

      processedTracks.push({
        ...track,
        img_url: track.img_url ? getFullImageUrl(track.img_url) : null,
        artist: artist,
      });
    }

    this.likedTracks = processedTracks;
  }

  async setRecentAlbums(albums) {
    // Преобразуем все URL изображений в альбомах
    const processedAlbums = [];

    for (const album of albums) {
      let artist = album.artist;

      if (artist && artist.email) {
        // Получаем пользователя для артиста
        const user = await this.fetchArtistUser(artist.email);

        // Добавляем информацию о пользователе к артисту
        artist = {
          ...artist,
          img_cover_url: artist.img_cover_url
            ? getFullImageUrl(artist.img_cover_url)
            : null,
          user: user,
        };
      }

      processedAlbums.push({
        ...album,
        img_url: album.img_url ? getFullImageUrl(album.img_url) : null,
        artist: artist,
      });
    }

    this.recentAlbums = processedAlbums;
  }

  async setLikedAlbums(albums) {
    console.log(
      "setLikedAlbums: Начинаем обработку альбомов, получено:",
      albums.length
    );

    // Преобразуем все URL изображений в альбомах
    const processedAlbums = [];

    for (const album of albums) {
      console.log("setLikedAlbums: Обрабатываем альбом:", album);

      let artist = album.artist;
      console.log("setLikedAlbums: Информация об исполнителе:", artist);

      if (artist && artist.email) {
        console.log(
          "setLikedAlbums: Получаем пользователя для исполнителя с email:",
          artist.email
        );
        // Получаем пользователя для артиста
        const user = await this.fetchArtistUser(artist.email);
        console.log("setLikedAlbums: Получен пользователь:", user);

        // Добавляем информацию о пользователе к артисту
        artist = {
          ...artist,
          img_cover_url: artist.img_cover_url
            ? getFullImageUrl(artist.img_cover_url)
            : null,
          user: user,
        };
        console.log(
          "setLikedAlbums: Обновленная информация об исполнителе:",
          artist
        );
      }

      const processedAlbum = {
        ...album,
        img_url: album.img_url ? getFullImageUrl(album.img_url) : null,
        artist: artist,
      };

      console.log("setLikedAlbums: Обработанный альбом:", processedAlbum);
      processedAlbums.push(processedAlbum);
    }

    console.log("setLikedAlbums: Все обработанные альбомы:", processedAlbums);
    this.likedAlbums = processedAlbums;
    console.log("setLikedAlbums: Установлено в this.likedAlbums");
  }

  setLoading(status) {
    this.isLoading = status;
  }

  setError(error) {
    this.error = error;
  }

  async fetchRecentData() {
    this.setLoading(true);
    this.setError(null);

    try {
      // Получаем последние треки
      const tracksResponse = await instance.get("recent/tracks/");
      await this.setRecentTracks(tracksResponse.data);

      // Получаем последние альбомы
      const albumsResponse = await instance.get(
        "recent/albums/?exclude_empty=true"
      );
      await this.setRecentAlbums(albumsResponse.data);
    } catch (error) {
      console.error("Ошибка при получении данных:", error);
      this.setError("Не удалось загрузить данные");
    } finally {
      this.setLoading(false);
    }
  }

  async fetchLikedTracks() {
    this.setLoading(true);
    this.setError(null);

    try {

      const response = await instance.get(
        "user-activities/?activity_type=like"
      );
      console.log("Получены активности:", response.data);

      // Извлекаем треки из активностей
      const tracks = response.data
        .filter((activity) => activity.track)
        .map((activity) => activity.track);

      console.log("Извлеченные треки:", tracks);

      await this.setLikedTracks(tracks);
      return tracks;
    } catch (error) {
      console.error("Ошибка при получении понравившихся треков:", error);
      this.setError("Не удалось загрузить понравившиеся треки");
      return [];
    } finally {
      this.setLoading(false);
    }
  }

  async fetchLikedAlbums() {
    this.setLoading(true);
    this.setError(null);

    try {
      console.log("fetchLikedAlbums: Начинаем запрос лайкнутых альбомов");
      // Получаем лайкнутые альбомы текущего пользователя через API активностей
      const response = await instance.get(
        "user-activities/?activity_type=like_album"
      );
      console.log("fetchLikedAlbums: Получен ответ от API:", response);
      console.log("fetchLikedAlbums: Данные активностей:", response.data);

      // Проверяем, что получены корректные данные
      if (!Array.isArray(response.data)) {
        console.error(
          "fetchLikedAlbums: Получены некорректные данные, ожидался массив"
        );
        this.setError("Получены некорректные данные активностей");
        this.setLoading(false);
        return [];
      }

      // Проверим, что в ответе есть активности с полем album
      const activitiesWithAlbum = response.data.filter(
        (activity) => activity.album
      );
      console.log(
        `fetchLikedAlbums: Найдено ${activitiesWithAlbum.length} активностей с альбомами из ${response.data.length} общих`
      );

      if (activitiesWithAlbum.length === 0) {
        console.warn(
          "fetchLikedAlbums: В данных активностей не найдены альбомы"
        );

        // Если активности есть, но альбомов нет, попробуем получить id альбомов
        // и загрузить их напрямую
        const albumIds = response.data
          .filter((activity) => activity.album_id || activity.album)
          .map(
            (activity) =>
              activity.album_id || (activity.album ? activity.album.id : null)
          )
          .filter((id) => id !== null);

        console.log(
          `fetchLikedAlbums: Найдено ${albumIds.length} ID альбомов из активностей`
        );

        if (albumIds.length > 0) {
          // Загрузим альбомы по их ID
          const albums = [];
          for (const albumId of albumIds) {
            try {
              const album = await this.fetchAlbumById(albumId);
              if (album) {
                albums.push(album);
              }
            } catch (err) {
              console.error(
                `Ошибка при загрузке альбома с ID ${albumId}:`,
                err
              );
            }
          }

          console.log(
            `fetchLikedAlbums: Загружено ${albums.length} альбомов напрямую`
          );
          this.likedAlbums = albums;
          return albums;
        }
      }

      // Извлекаем альбомы из активностей
      const albums = activitiesWithAlbum.map((activity) => activity.album);
      console.log("fetchLikedAlbums: Извлечено альбомов:", albums.length);
      console.log("fetchLikedAlbums: Детали альбомов:", albums);

      // Устанавливаем лайкнутые альбомы в состояние
      await this.setLikedAlbums(albums);

      console.log(
        "fetchLikedAlbums: После установки this.likedAlbums =",
        this.likedAlbums
      );
      return albums;
    } catch (error) {
      console.error("Ошибка при получении понравившихся альбомов:", error);
      console.error("Детали ошибки:", error.response?.data || error.message);
      this.setError("Не удалось загрузить понравившиеся альбомы");
      return [];
    } finally {
      this.setLoading(false);
    }
  }

  async likeTrack(trackId) {
    try {
      const response = await instance.post(`tracks/${trackId}/like/`);

      // Обновляем данные о лайкнутых треках
      await this.fetchLikedTracks();

      return response.data;
    } catch (error) {
      console.error("Ошибка при добавлении лайка:", error);
      throw error;
    }
  }

  async unlikeTrack(trackId) {
    try {
      console.log(`Отправляем запрос DELETE на tracks/${trackId}/unlike/`);
      // Используем правильный API endpoint для удаления лайка
      const response = await instance.delete(`tracks/${trackId}/unlike/`);
      console.log("Ответ от сервера:", response.data);

      // Удаляем трек из списка лайкнутых
      this.likedTracks = this.likedTracks.filter(
        (track) => track.id !== trackId
      );

      return response.data;
    } catch (error) {
      console.error("Ошибка при удалении лайка:", error);
      console.error("Детали ошибки:", error.response?.data || error.message);
      throw error;
    }
  }

  async likeAlbum(albumId) {
    try {
      const response = await instance.post(`albums/${albumId}/like/`);

      // Обновляем данные о лайкнутых альбомах
      await this.fetchLikedAlbums();

      return response.data;
    } catch (error) {
      console.error("Ошибка при добавлении лайка альбому:", error);
      throw error;
    }
  }

  async unlikeAlbum(albumId) {
    try {
      console.log(`Отправляем запрос DELETE на albums/${albumId}/unlike/`);
      // Используем правильный API endpoint для удаления лайка
      const response = await instance.delete(`albums/${albumId}/unlike/`);
      console.log("Ответ от сервера:", response.data);

      // Удаляем альбом из списка лайкнутых
      this.likedAlbums = this.likedAlbums.filter(
        (album) => album.id !== albumId
      );

      return response.data;
    } catch (error) {
      console.error("Ошибка при удалении лайка альбома:", error);
      console.error("Детали ошибки:", error.response?.data || error.message);
      throw error;
    }
  }

  async loadAndPlayMusic(name) {
    try {
      const response = await fetch(
        `http://localhost:3000/music/stream/${name}`
      );
      if (!response.ok) {
        throw new Error("Failed to load music file");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      return url;
    } catch (error) {
      console.error("Error loading music file:", error);
      throw error;
    }
  }

  async fetchAlbumById(albumId) {
    this.setLoading(true);
    this.setError(null);

    try {
      console.log(`Получаем альбом с ID: ${albumId}`);
      const response = await instance.get(`albums/${albumId}/`);

      let album = response.data;
      let artist = album.artist;

      if (artist && artist.email) {
        // Получаем пользователя для артиста
        const user = await this.fetchArtistUser(artist.email);

        // Добавляем информацию о пользователе к артисту
        artist = {
          ...artist,
          img_cover_url: artist.img_cover_url
            ? getFullImageUrl(artist.img_cover_url)
            : null,
          user: user,
        };
      }

      // Обрабатываем URL изображения альбома
      album = {
        ...album,
        img_url: album.img_url ? getFullImageUrl(album.img_url) : null,
        artist: artist,
      };

      return album;
    } catch (error) {
      console.error(`Ошибка при получении альбома с ID ${albumId}:`, error);
      this.setError("Не удалось загрузить альбом");
      return null;
    } finally {
      this.setLoading(false);
    }
  }

  async fetchAlbumTracks(albumId) {
    this.setLoading(true);
    this.setError(null);

    try {
      console.log(`Получаем треки альбома с ID: ${albumId}`);
      const response = await instance.get(`albums/${albumId}/tracks/`);

      // Обрабатываем треки аналогично другим методам
      const processedTracks = [];

      for (const track of response.data) {
        let artist = track.artist;

        if (artist && artist.email) {
          // Получаем пользователя для артиста
          const user = await this.fetchArtistUser(artist.email);

          // Добавляем информацию о пользователе к артисту
          artist = {
            ...artist,
            img_cover_url: artist.img_cover_url
              ? getFullImageUrl(artist.img_cover_url)
              : null,
            user: user,
          };
        }

        processedTracks.push({
          ...track,
          img_url: track.img_url ? getFullImageUrl(track.img_url) : null,
          artist: artist,
        });
      }

      return processedTracks;
    } catch (error) {
      console.error(
        `Ошибка при получении треков альбома с ID ${albumId}:`,
        error
      );
      this.setError("Не удалось загрузить треки альбома");
      return [];
    } finally {
      this.setLoading(false);
    }
  }

  async isTrackLiked(trackId) {
    try {
      // Проверяем, есть ли трек в лайкнутых
      const likedTracks = toJS(this.likedTracks);
      return likedTracks.some((track) => track.id === trackId);
    } catch (error) {
      console.error("Ошибка при проверке лайка трека:", error);
      return false;
    }
  }

  async isAlbumLiked(albumId) {
    try {
      // Проверяем, есть ли альбом в лайкнутых
      const likedAlbums = toJS(this.likedAlbums);
      return likedAlbums.some((album) => album.id === albumId);
    } catch (error) {
      console.error("Ошибка при проверке лайка альбома:", error);
      return false;
    }
  }
}

const homeStore = new HomeStore();

export default homeStore;
