import { observer } from "mobx-react-lite";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import homeStore from "../../stores/homeStore";
import authStore from "../../stores/authStore";
import MiniPlayer from "../MiniPlayer/component";
import instance from "../../axios/axios";
import { toJS } from "mobx";
import { getFullImageUrl } from "../../utils/imageUtils";

import styles from "./Playlists.module.scss";
import UploadIcon from "../Home/components/UploadIcon";

const Playlists = observer(() => {
  const navigate = useNavigate();
  const [src, setSrc] = useState("");
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [trackName, setTrackName] = useState("");
  const [author, setAuthor] = useState("");
  const [activeTrackId, setActiveTrackId] = useState(null);
  const [directAlbums, setDirectAlbums] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTrack, setCurrentTrack] = useState(null);

  const likedAlbums = toJS(homeStore.likedAlbums) || [];
  const isLoading = homeStore.isLoading;
  const user = authStore.user;
  const isArtist = authStore.isArtist;

  // Добавляем отладочные логи для понимания данных
  console.log("Текущее состояние likedAlbums:", likedAlbums);
  console.log("Текущее состояние directAlbums:", directAlbums);
  console.log("Состояние isLoading:", isLoading);
  console.log("Ошибка если есть:", error);

  // Прямой запрос альбомов из активностей пользователя
  const fetchAlbumsDirectly = async () => {
    try {
      console.log("Выполняем прямой запрос альбомов");

      // Проверяем токен авторизации
      const token =
        localStorage.getItem("token") || localStorage.getItem("authToken");
      if (!token) {
        console.error(
          "Токен авторизации отсутствует при прямом запросе альбомов"
        );
        return;
      }

      // Получаем лайкнутые альбомы через API активностей с явным заголовком авторизации
      const response = await fetch(
        "http://localhost:8000/api/user-activities/?activity_type=like_album",
        {
          headers: {
            Authorization: `Token ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }

      const data = await response.json();
      console.log("Получены активности (прямой запрос):", data);

      // Извлекаем объекты альбомов из активностей
      const albums = [];
      for (const activity of data) {
        if (activity.album) {
          // Если у активности есть полный объект альбома
          const album = activity.album;

          // Обработка URL изображения
          if (album.img_url) {
            // Проверяем и корректируем URL изображения
            if (!album.img_url.startsWith("http")) {
              album.img_url = `http://localhost:8000${
                album.img_url.startsWith("/") ? "" : "/"
              }${album.img_url}`;
            }
          }

          // Обработка данных исполнителя
          if (album.artist) {
            const artist = album.artist;

            // Обработка URL изображения исполнителя
            if (
              artist.img_cover_url &&
              !artist.img_cover_url.startsWith("http")
            ) {
              artist.img_cover_url = `http://localhost:8000${
                artist.img_cover_url.startsWith("/") ? "" : "/"
              }${artist.img_cover_url}`;
            }

            // Добавляем подробности о пользователе исполнителя, если их нет
            if (!artist.user && artist.email) {
              try {
                const userResponse = await fetch(
                  `http://localhost:8000/api/users/?search=${encodeURIComponent(
                    artist.email
                  )}`,
                  {
                    headers: {
                      Authorization: `Token ${token}`,
                    },
                  }
                );

                if (userResponse.ok) {
                  const userData = await userResponse.json();
                  if (userData && userData.length > 0) {
                    artist.user = userData[0];
                  }
                }
              } catch (err) {
                console.error(
                  "Ошибка при получении пользователя для исполнителя:",
                  err
                );
              }
            }
          }

          // Добавляем альбом в список, предварительно проверив, что такого еще нет
          if (!albums.some((a) => a.id === album.id)) {
            albums.push(album);
          }
        } else if (activity.album_id) {
          // Если есть только ID альбома, но нет самого объекта альбома
          try {
            const albumResponse = await fetch(
              `http://localhost:8000/api/albums/${activity.album_id}/`,
              {
                headers: {
                  Authorization: `Token ${token}`,
                },
              }
            );

            if (albumResponse.ok) {
              const album = await albumResponse.json();

              // Обработка URL изображения
              if (album.img_url && !album.img_url.startsWith("http")) {
                album.img_url = `http://localhost:8000${
                  album.img_url.startsWith("/") ? "" : "/"
                }${album.img_url}`;
              }

              // Добавляем альбом в список, предварительно проверив, что такого еще нет
              if (!albums.some((a) => a.id === album.id)) {
                albums.push(album);
              }
            }
          } catch (err) {
            console.error(
              `Ошибка при получении альбома с ID ${activity.album_id}:`,
              err
            );
          }
        }
      }

      console.log("Обработаны альбомы напрямую:", albums);
      setDirectAlbums(albums);
    } catch (error) {
      console.error("Ошибка при прямой загрузке альбомов:", error);
    }
  };

  useEffect(() => {
    if (!authStore.isAuthenticated) {
      navigate("/auth");
      return;
    }

    // Загружаем плейлисты пользователя
    fetchPlaylists();

    // Загружаем лайкнутые альбомы
    homeStore.fetchLikedAlbums();
  }, [navigate]);

  const fetchPlaylists = async () => {
    try {
      setLoading(true);
      const response = await instance.get("/playlists/");
      setPlaylists(response.data);
      setError(null);
    } catch (err) {
      setError("Ошибка при загрузке плейлистов");
      console.error("Ошибка:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlaylist = () => {
    navigate("/playlists/create");
  };

  const handleEditPlaylist = (playlistId) => {
    navigate(`/playlists/${playlistId}/edit`);
  };

  const handleDeletePlaylist = async (playlistId) => {
    if (window.confirm("Вы уверены, что хотите удалить этот плейлист?")) {
      try {
        await instance.delete(`/playlists/${playlistId}/`);
        fetchPlaylists();
      } catch (err) {
        setError("Ошибка при удалении плейлиста");
        console.error("Ошибка:", err);
      }
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  // Выбираем, какие альбомы отображать: из store или полученные напрямую
  const albumsToDisplay = likedAlbums.length > 0 ? likedAlbums : directAlbums;

  // Проверяем, что все альбомы имеют необходимые поля
  const validAlbums = albumsToDisplay.filter((album) => {
    if (!album || typeof album !== "object") return false;
    if (!album.id) return false;
    if (!album.title) return false;
    return true;
  });

  console.log("Валидные альбомы для отображения:", validAlbums);

  return (
    <div className={styles.mainContainer}>
      <div className={styles.appContent}>
        <div className={styles.contentArea}>
          <main className={styles.content}>
            {/* Секция плейлистов пользователя */}
            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2>Мои плейлисты</h2>
                <button
                  onClick={handleCreatePlaylist}
                  className={styles.createButton}
                >
                  Создать плейлист
                </button>
              </div>

              {loading ? (
                <div className={styles.loading}>Загрузка...</div>
              ) : error ? (
                <div className={styles.error}>{error}</div>
              ) : playlists.length === 0 ? (
                <div className={styles.emptyState}>
                  <p>У вас пока нет плейлистов</p>
                  <button
                    onClick={handleCreatePlaylist}
                    className={styles.createButton}
                  >
                    Создать первый плейлист
                  </button>
                </div>
              ) : (
                <div className={styles.playlistsGrid}>
                  {playlists.map((playlist) => (
                    <div key={playlist.id} className={styles.playlistCard}>
                      <div
                        className={styles.playlistImageContainer}
                        onClick={() => navigate(`/playlists/${playlist.id}`)}
                      >
                        {playlist.cover_image ? (
                          <img
                            src={playlist.cover_image}
                            alt={playlist.title}
                            className={styles.playlistImage}
                          />
                        ) : (
                          <div className={styles.noPlaylistImage}>
                            <span>🎵</span>
                          </div>
                        )}
                      </div>
                      <div
                        className={styles.playlistInfo}
                        onClick={() => navigate(`/playlists/${playlist.id}`)}
                      >
                        <h3 className={styles.playlistTitle}>
                          {playlist.title}
                        </h3>
                        <p className={styles.playlistDescription}>
                          {playlist.description || "Нет описания"}
                        </p>
                        <p className={styles.trackCount}>
                          Треков: {playlist.tracks_count || 0}
                        </p>
                      </div>
                      <div className={styles.playlistActions}>
                        {/* <button
                          onClick={() => handleEditPlaylist(playlist.id)}
                          className={styles.editButton}
                        >
                          Редактировать
                        </button> */}
                        <button
                          onClick={() => handleDeletePlaylist(playlist.id)}
                          className={styles.deleteButton}
                        >
                          Удалить
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Секция избранных альбомов */}
            <section className={styles.section}>
              <h2>Избранные альбомы</h2>
              {isLoading ? (
                <div className={styles.loading}>Загрузка...</div>
              ) : likedAlbums.length === 0 ? (
                <div className={styles.emptyState}>
                  У вас пока нет избранных альбомов
                </div>
              ) : (
                <div className={styles.albumsGrid}>
                  {likedAlbums.map((album) => (
                    <div
                      key={album.id}
                      className={styles.albumCard}
                      onClick={() => navigate(`/album/${album.id}`)}
                    >
                      <div className={styles.albumImageContainer}>
                        {album.img_url ? (
                          <img
                            src={album.img_url}
                            alt={album.title}
                            className={styles.albumImage}
                            onError={(e) => {
                              e.target.onerror = null;
                              e.target.style.display = "none";
                              e.target.parentNode.querySelector(
                                "." + styles.noAlbumImage
                              ).style.display = "flex";
                            }}
                          />
                        ) : (
                          <div className={styles.noAlbumImage}>
                            <span>🎵</span>
                          </div>
                        )}
                      </div>
                      <div className={styles.albumInfo}>
                        <h3 className={styles.albumTitle}>{album.title}</h3>
                        <p className={styles.albumArtist}>
                          {album.artist?.user?.username ||
                            "Неизвестный исполнитель"}
                        </p>
                        <p className={styles.albumTracks}>
                          Треков: {album.total_tracks || 0}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </main>
        </div>
      </div>

      <div className={styles.playerContainer}>
        <MiniPlayer
          trackName={currentTrack?.title || ""}
          author={currentTrack?.artist || ""}
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
        />
      </div>
    </div>
  );
});

export default Playlists;
