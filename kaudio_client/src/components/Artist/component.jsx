import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import axios from "../../axios/axios.js";
import styles from "./styles.module.scss";
import instance from "../../axios/axios";
import { observer } from "mobx-react-lite";
import authStore from "../../stores/authStore";
import MiniPlayer from "../MiniPlayer/component";
import { toJS } from "mobx";
import UploadIcon from "../Home/components/UploadIcon";

const Artist = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [artist, setArtist] = useState(null);
  const [albums, setAlbums] = useState([]);
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTrackId, setActiveTrackId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [src, setSrc] = useState("");
  const [trackName, setTrackName] = useState("");
  const [author, setAuthor] = useState("");
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);

  const user = authStore.user;
  const isArtist = authStore.isArtist;

  useEffect(() => {
    // Проверяем, авторизован ли пользователь
    if (!authStore.isAuthenticated) {
      console.log("Пользователь не авторизован, перенаправляем на /auth");
      navigate("/auth");
      return;
    }

    const fetchArtistData = async () => {
      try {
        setLoading(true);
        // Получаем данные о самом артисте
        const artistResponse = await axios.get(`/artists/${id}/`);
        const artist = artistResponse.data;

        // Если у артиста есть email, пытаемся найти пользователя
        if (artist.email) {
          try {
            const userResponse = await axios.get(
              `/users/?email=${artist.email}`
            );
            if (userResponse.data && userResponse.data.length > 0) {
              // Нашли пользователя по email
              artist.user = userResponse.data[0];
              console.log("Найден пользователь для артиста:", artist.user);
            }
          } catch (err) {
            console.error("Ошибка при поиске пользователя для артиста:", err);
          }
        }

        setArtist(artist);

        // Получаем альбомы артиста
        const albumsResponse = await axios.get(`/artists/${id}/albums/`);
        setAlbums(albumsResponse.data);

        // Получаем треки артиста (не входящие в альбомы)
        const tracksResponse = await axios.get(`/artists/${id}/tracks/`);
        setTracks(tracksResponse.data);

        setLoading(false);
      } catch (error) {
        console.error("Ошибка при загрузке данных артиста:", error);
        setLoading(false);
      }
    };

    if (id) {
      fetchArtistData();
    }
  }, [id, navigate]);

  // Проверка и исправление URL изображений
  const fixImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    console.log("url alboma", url);
    return `http://localhost:8000${url.startsWith("/") ? "" : "/"}${url}`;
  };

  // Загрузка и воспроизведение трека из API
  const handlePlayTrack = async (track, index) => {
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
    if (tracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex > 0 ? currentTrackIndex - 1 : tracks.length - 1;

    handlePlayTrack(tracks[newIndex], newIndex);
  };

  const handleNextTrack = () => {
    if (tracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex < tracks.length - 1 ? currentTrackIndex + 1 : 0;

    handlePlayTrack(tracks[newIndex], newIndex);
  };

  // Обработчик клика по профилю пользователя
  const handleProfileClick = () => {
    navigate("/settings");
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (!artist) {
    return <div className={styles.error}>Артист не найден</div>;
  }

  // Получаем имя артиста, предпочитая никнейм пользователя, связанного с артистом
  const artistName =
    artist.user?.username ||
    (artist.nickname
      ? artist.nickname
      : artist.name
      ? artist.name
      : artist.display_name
      ? artist.display_name
      : artist.email
      ? artist.email
      : "Неизвестный артист");
  const avatarUrl = fixImageUrl(artist.img_cover_url);
  const artistDescription = artist.bio || "";

  return (
    <div className={styles.mainContainer}>
      <div className={styles.appContent}>
        <div className={styles.contentArea}>
          <main className={styles.content}>
            <div className={styles.artistPage}>
              <div className={styles.artistHeader}>
                <div className={styles.artistAvatar}>
                  {avatarUrl ? (
                    <img src={avatarUrl} alt={artistName} />
                  ) : (
                    <div className={styles.defaultAvatar}>{artistName[0]}</div>
                  )}
                </div>
                <div className={styles.artistInfo}>
                  <h1 className={styles.artistName}>{artistName}</h1>

                  <div className={styles.artistStats}>
                    {artist.is_verified && (
                      <span
                        className={styles.verifiedBadge}
                        title="Верифицированный артист"
                      >
                        ✓
                      </span>
                    )}
                    {artist.monthly_listeners > 0 && (
                      <span className={styles.listeners}>
                        {artist.monthly_listeners.toLocaleString()} ежемесячных
                        слушателей
                      </span>
                    )}
                  </div>

                  {artist.genres && artist.genres.length > 0 && (
                    <div className={styles.genres}>
                      {artist.genres.map((genre) => (
                        <span key={genre.id || genre} className={styles.genre}>
                          {genre.name || genre}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className={styles.artistDescription}>
                    {artistDescription}
                  </p>
                </div>
              </div>

              {albums.length > 0 && (
                <div className={styles.section}>
                  <h2 className={styles.sectionTitle}>Альбомы</h2>
                  <div className={styles.albumsGrid}>
                    {albums.map((album) => (
                      <Link
                        to={`/album/${album.id}`}
                        key={album.id}
                        className={styles.albumCard}
                      >
                        <div className={styles.albumCover}>
                          {album.img_url ? (
                            <img
                              src={fixImageUrl(album.img_url)}
                              alt={album.title}
                            />
                          ) : (
                            <div className={styles.defaultCover}></div>
                          )}
                        </div>
                        <h3 className={styles.albumTitle}>{album.title}</h3>
                        <p className={styles.albumYear}>
                          {new Date(album.release_date).getFullYear()}
                        </p>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {tracks.length > 0 && (
                <div className={styles.section}>
                  <h2 className={styles.sectionTitle}>Популярные треки</h2>
                  <div className={styles.trackList}>
                    {tracks.map((track, index) => (
                      <div
                        key={track.id}
                        className={`${styles.trackItem} ${
                          activeTrackId === track.id ? styles.activeTrack : ""
                        }`}
                        onClick={() => handlePlayTrack(track, index)}
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
                          <div className={styles.trackDuration}>
                            {Math.floor(track.duration / 60)}:
                            {(track.duration % 60).toString().padStart(2, "0")}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>

      <div className={styles.playerContainer}>
        <MiniPlayer
          trackName={trackName}
          author={artistName}
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

export default Artist;
