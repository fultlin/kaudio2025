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

  const likedAlbums = toJS(homeStore.likedAlbums) || [];
  const isLoading = homeStore.isLoading;
  const error = homeStore.error;
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
    // Проверяем, авторизован ли пользователь
    if (!authStore.isAuthenticated) {
      console.log("Пользователь не авторизован, перенаправляем на /auth");
      navigate("/auth");
      return;
    }

    console.log("Начинаем загрузку лайкнутых альбомов");

    // Запускаем прямой запрос альбомов независимо от результата запроса через store
    fetchAlbumsDirectly();

    // Также загружаем лайкнутые альбомы через store для синхронизации состояния
    homeStore
      .fetchLikedAlbums()
      .then((albums) => {
        console.log(`Получено ${albums.length} лайкнутых альбомов через store`);
        console.log("Данные альбомов из store:", albums);
      })
      .catch((error) => {
        console.error(
          "Ошибка при загрузке лайкнутых альбомов через store:",
          error
        );
      });
  }, [navigate]);

  // Обработчик клика по альбому
  const handleAlbumClick = (albumId) => {
    // Переходим на страницу альбома
    navigate(`/album/${albumId}`);
  };

  // Обработчик клика по профилю пользователя
  const handleProfileClick = () => {
    navigate("/settings");
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handlePrevTrack = () => {
    // Логика переключения на предыдущий трек
  };

  const handleNextTrack = () => {
    // Логика переключения на следующий трек
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
        <div className={styles.sidebar}>
          <div className={styles.sidebarHeader}>
            <h2>KAudio</h2>
          </div>

          {user && (
            <div className={styles.userProfile} onClick={handleProfileClick}>
              <div className={styles.profileImage}>
                {user.img_profile_url ? (
                  <img src={user.img_profile_url} alt={user.username} />
                ) : (
                  <div className={styles.defaultAvatar}>
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div className={styles.profileInfo}>
                <h3>{user.username}</h3>
                <p>{isArtist ? "Артист" : "Слушатель"}</p>
              </div>
            </div>
          )}

          <nav className={styles.sidebarNav}>
            <Link to="/" className={styles.navLink}>
              <span className={styles.navIcon}>🏠</span>
              <span>Главная</span>
            </Link>
            <Link to="/music" className={styles.navLink}>
              <span className={styles.navIcon}>🎵</span>
              <span>Моя музыка</span>
            </Link>
            <Link
              to="/playlists"
              className={styles.navLink + " " + styles.active}
            >
              <span className={styles.navIcon}>📑</span>
              <span>Плейлисты</span>
            </Link>
            <Link to="/settings" className={styles.navLink}>
              <span className={styles.navIcon}>⚙️</span>
              <span>Настройки</span>
            </Link>
          </nav>

          <div className={styles.uploadWrapper}>
            <Link to="/upload" className={styles.uploadButton}>
              <UploadIcon />
              <span>Загрузить</span>
            </Link>
          </div>
        </div>

        <div className={styles.contentArea}>
          <main className={styles.content}>
            {/* Отладочная информация */}
            {process.env.NODE_ENV === "development" && (
              <div
                style={{
                  marginBottom: "20px",
                  padding: "10px",
                  backgroundColor: "rgba(0,0,0,0.2)",
                  borderRadius: "5px",
                }}
              >
                <h3 style={{ marginTop: 0 }}>Отладочная информация:</h3>
                <div>
                  <p>Пользователь: {user ? user.username : "не авторизован"}</p>
                  <p>Загрузка: {isLoading ? "Да" : "Нет"}</p>
                  <p>Ошибка: {error || "нет"}</p>
                  <p>Лайкнутые альбомы (store): {likedAlbums.length}</p>
                  <p>Альбомы (прямой запрос): {directAlbums.length}</p>
                  <button
                    onClick={fetchAlbumsDirectly}
                    style={{
                      padding: "5px 10px",
                      backgroundColor: "#1db954",
                      color: "white",
                      border: "none",
                      borderRadius: "5px",
                      cursor: "pointer",
                    }}
                  >
                    Обновить альбомы
                  </button>
                </div>
              </div>
            )}

            {/* Секция: Избранные альбомы */}
            <section className={styles.section}>
              <h2>Избранные альбомы</h2>
              {isLoading && directAlbums.length === 0 ? (
                <div className={styles.loading}>Загрузка...</div>
              ) : error && directAlbums.length === 0 ? (
                <div className={styles.error}>{error}</div>
              ) : (
                <div className={styles.albumsGrid}>
                  {validAlbums.length > 0 ? (
                    validAlbums.map((album) => (
                      <div
                        key={album.id}
                        className={styles.albumCard}
                        onClick={() => handleAlbumClick(album.id)}
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
                          <div
                            className={styles.noAlbumImage}
                            style={{ display: album.img_url ? "none" : "flex" }}
                          >
                            <span>🎵</span>
                          </div>
                        </div>
                        <div className={styles.albumInfo}>
                          <h3 className={styles.albumTitle}>{album.title}</h3>
                          <p className={styles.albumArtist}>
                            {album.artist?.user?.username ||
                              album.artist?.email ||
                              "Неизвестный исполнитель"}
                          </p>
                          <p className={styles.albumTracks}>
                            Треков: {album.total_tracks || 0}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className={styles.emptyState}>
                      У вас пока нет избранных альбомов
                    </div>
                  )}
                </div>
              )}
            </section>
          </main>
        </div>
      </div>

      <div className={styles.playerContainer}>
        <MiniPlayer
          trackName={trackName}
          author={author}
          name={src}
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
          onPrev={handlePrevTrack}
          onNext={handleNextTrack}
        />
      </div>
    </div>
  );
});

export default Playlists;
