import { observer } from "mobx-react-lite";
import MiniPlayer from "../MiniPlayer/component";
import { Link, useNavigate } from "react-router-dom";
import homeStore from "stores/homeStore";
import { toJS } from "mobx";
import { useEffect, useState } from "react";
import instance from "../../axios/axios";
import axios from "axios";
import authStore from "../../stores/authStore";
import { ArrowRight, Search, Filter } from "lucide-react";

import styles from "./Home.module.scss";
import UploadIcon from "./components/UploadIcon";

const Home = observer(() => {
  const navigate = useNavigate();
  const [src, setSrc] = useState("");
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [trackName, setTrackName] = useState("");
  const [author, setAuthor] = useState("");
  const [activeTrackId, setActiveTrackId] = useState(null);

  // Новые состояния для фильтрации и сортировки
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [filterGenre, setFilterGenre] = useState("all");
  const [genres, setGenres] = useState([]);

  const recentTracks = toJS(homeStore.recentTracks) || [];
  const recentAlbums = toJS(homeStore.recentAlbums) || [];
  const likedTracks = toJS(homeStore.likedTracks) || [];
  const isLoading = homeStore.isLoading;
  const error = homeStore.error;
  const user = authStore.user;
  const isArtist = authStore.isArtist;

  useEffect(() => {
    // Загружаем последние треки и альбомы при монтировании компонента
    homeStore.fetchRecentData();
    // Загружаем лайкнутые треки
    if (authStore.isAuthenticated) {
      homeStore.fetchLikedTracks();
    }
    // Загружаем список жанров
    fetchGenres();
  }, []);

  // Функция для загрузки жанров
  const fetchGenres = async () => {
    try {
      const response = await instance.get("genres/");
      setGenres(response.data);
    } catch (error) {
      console.error("Ошибка при загрузке жанров:", error);
    }
  };

  // Проверка, лайкнут ли трек
  const isTrackLiked = (trackId) => {
    console.log(`Проверка статуса лайка для трека ${trackId}`);
    console.log(
      `Список лайкнутых треков:`,
      likedTracks.map((track) => track.id)
    );
    return likedTracks.some((track) => track.id === trackId);
  };

  // Обработчик лайка/анлайка трека
  const handleLikeTrack = async (e, trackId) => {
    e.stopPropagation(); // Предотвращаем воспроизведение трека при клике на лайк

    if (!authStore.isAuthenticated) {
      // Если пользователь не авторизован, перенаправляем на страницу входа
      navigate("/auth");
      return;
    }

    try {
      console.log(`Обработка лайка для трека с ID: ${trackId}`);
      console.log(
        `Текущий статус лайка: ${
          isTrackLiked(trackId) ? "лайкнут" : "не лайкнут"
        }`
      );

      if (isTrackLiked(trackId)) {
        console.log(`Удаляем лайк у трека ${trackId}`);
        await homeStore.unlikeTrack(trackId);
        console.log(`Лайк успешно удален у трека ${trackId}`);
      } else {
        console.log(`Добавляем лайк треку ${trackId}`);
        await homeStore.likeTrack(trackId);
        console.log(`Лайк успешно добавлен треку ${trackId}`);
      }
    } catch (error) {
      console.error("Ошибка при обработке лайка:", error);
    }
  };

  // Загрузка и воспроизведение трека из API
  const handlePlayAPITrack = async (track, index) => {
    try {
      if (activeTrackId === track.id && isPlaying) {
        // Если тот же трек уже играет, то ставим на паузу
        setIsPlaying(false);
        return;
      }

      if (activeTrackId === track.id && !isPlaying) {
        // Если тот же трек на паузе, то продолжаем воспроизведение
        setIsPlaying(true);
        return;
      }

      // Загружаем аудиофайл трека
      const response = await instance.get(`tracks/${track.id}/stream/`, {
        responseType: "blob",
      });

      // Создаем URL для воспроизведения
      const audioUrl = URL.createObjectURL(response.data);

      // Обновляем данные для плеера
      setSrc(audioUrl);
      setTrackName(track.title);
      setAuthor(
        track.artist
          ? track.artist.user?.username || track.artist.email
          : "Неизвестный исполнитель"
      );
      setCurrentTrackIndex(index);
      setActiveTrackId(track.id);
      setIsPlaying(true);

      // Увеличиваем счетчик прослушиваний
      await instance.post(`tracks/${track.id}/play/`);
    } catch (error) {
      console.error("Ошибка при воспроизведении трека:", error);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handlePrevTrack = () => {
    if (recentTracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex > 0 ? currentTrackIndex - 1 : recentTracks.length - 1;

    handlePlayAPITrack(recentTracks[newIndex], newIndex);
  };

  const handleNextTrack = () => {
    if (recentTracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex < recentTracks.length - 1 ? currentTrackIndex + 1 : 0;

    handlePlayAPITrack(recentTracks[newIndex], newIndex);
  };

  // Обработчик клика по альбому
  const handleAlbumClick = (albumId) => {
    // Переходим на страницу альбома
    navigate(`/album/${albumId}`);
  };

  // Обработчик клика по профилю пользователя
  const handleProfileClick = () => {
    navigate("/settings");
  };

  // Функция для фильтрации и сортировки треков
  const getFilteredAndSortedTracks = () => {
    let filtered = [...recentTracks];

    // Фильтрация по поисковому запросу
    if (searchQuery) {
      filtered = filtered.filter(
        (track) =>
          track.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (track.artist?.user?.username || track.artist?.email || "")
            .toLowerCase()
            .includes(searchQuery.toLowerCase())
      );
    }

    // Фильтрация по жанру
    if (filterGenre !== "all") {
      filtered = filtered.filter((track) =>
        track.genres.some((genre) => genre.id === parseInt(filterGenre))
      );
    }

    // Сортировка
    switch (sortBy) {
      case "newest":
        filtered.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        break;
      case "oldest":
        filtered.sort(
          (a, b) => new Date(a.created_at) - new Date(b.created_at)
        );
        break;
      case "name":
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "popular":
        filtered.sort((a, b) => (b.plays || 0) - (a.plays || 0));
        break;
      default:
        break;
    }

    return filtered;
  };

  // Функция для фильтрации и сортировки альбомов
  const getFilteredAndSortedAlbums = () => {
    let filtered = [...recentAlbums];

    // Фильтрация по поисковому запросу
    if (searchQuery) {
      filtered = filtered.filter(
        (album) =>
          album.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (album.artist?.user?.username || album.artist?.email || "")
            .toLowerCase()
            .includes(searchQuery.toLowerCase())
      );
    }

    // Фильтрация по жанру
    if (filterGenre !== "all") {
      filtered = filtered.filter((album) =>
        album.genres.some((genre) => genre.id === parseInt(filterGenre))
      );
    }

    // Сортировка
    switch (sortBy) {
      case "newest":
        filtered.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        break;
      case "oldest":
        filtered.sort(
          (a, b) => new Date(a.created_at) - new Date(b.created_at)
        );
        break;
      case "name":
        filtered.sort((a, b) => a.title.localeCompare(b.title));
        break;
      case "popular":
        filtered.sort((a, b) => (b.plays || 0) - (a.plays || 0));
        break;
      default:
        break;
    }

    return filtered;
  };

  return (
    <div className={styles.mainContainer}>
      <button onClick={() => {throw new Error("This is your first error!");}}>Break the world</button>
      <div className={styles.appContent}>
        <div className={styles.contentArea}>
          <main className={styles.content}>
            {/* Фильтры и сортировка */}
            <div className={styles.filtersContainer}>

              <div className={styles.filterControls}>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className={styles.filterSelect}
                >
                  <option value="newest">Сначала новые</option>
                  <option value="oldest">Сначала старые</option>
                  <option value="name">По названию</option>
                  <option value="popular">По популярности</option>
                </select>

                <select
                  value={filterGenre}
                  onChange={(e) => setFilterGenre(e.target.value)}
                  className={styles.filterSelect}
                >
                  <option value="all">Все жанры</option>
                  {genres.map((genre) => (
                    <option key={genre.id} value={genre.id}>
                      {genre.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Секция: Последние треки */}
            <section className={styles.section}>
              <h2>Последние треки</h2>
              {isLoading ? (
                <div className={styles.loading}>Загрузка...</div>
              ) : error ? (
                <div className={styles.error}>{error}</div>
              ) : (
                <div className={styles.trackList}>
                  {getFilteredAndSortedTracks().length > 0 ? (
                    getFilteredAndSortedTracks().map((track, index) => (
                      <div
                        key={track.id}
                        onClick={() => handlePlayAPITrack(track, index)}
                        className={`${styles.trackItem} ${
                          activeTrackId === track.id ? styles.activeTrack : ""
                        }`}
                      >
                        <div className={styles.trackNumber}>{index + 1}</div>
                        <div className={styles.trackPlayButton}>
                          {activeTrackId === track.id && isPlaying ? (
                            <span className={styles.pauseIcon}>❚❚</span>
                          ) : (
                            <span className={styles.playIcon}>▶</span>
                          )}
                        </div>
                        <div className={styles.trackInfo}>
                          <div className={styles.trackTitle}>{track.title}</div>
                          <div className={styles.trackArtist}>
                            {track.artist ? (
                              <Link
                                to={`/artist/${track.artist.id}`}
                                className={styles.artistLink}
                                onClick={(e) => e.stopPropagation()}
                              >
                                {track.artist.user?.username ||
                                  track.artist.email ||
                                  "Неизвестный исполнитель"}
                              </Link>
                            ) : (
                              "Неизвестный исполнитель"
                            )}
                          </div>
                        </div>
                        <div className={styles.trackDuration}>
                          {Math.floor(track.duration / 60)}:
                          {String(track.duration % 60).padStart(2, "0")}
                        </div>
                        <div
                          className={styles.trackGoTo}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/tracks/${track.id}`);
                          }}
                          title="Перейти на страницу трека"
                        >
                          <ArrowRight size={20} />
                        </div>
                        <div
                          className={styles.trackLike}
                          onClick={(e) => handleLikeTrack(e, track.id)}
                        >
                          {isTrackLiked(track.id) ? (
                            <span className={styles.likedIcon}>❤️</span>
                          ) : (
                            <span className={styles.unlikedIcon}>🤍</span>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className={styles.emptyState}>
                      Нет доступных треков
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Секция: Последние альбомы */}
            <section className={styles.section}>
              <h2>Последние альбомы</h2>
              {isLoading ? (
                <div className={styles.loading}>Загрузка...</div>
              ) : error ? (
                <div className={styles.error}>{error}</div>
              ) : (
                <div className={styles.albumsGrid}>
                  {getFilteredAndSortedAlbums().length > 0 ? (
                    getFilteredAndSortedAlbums().map((album) => (
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
                      Нет доступных альбомов
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

export default Home;
