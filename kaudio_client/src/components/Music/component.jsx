import { observer } from "mobx-react-lite";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import homeStore from "stores/homeStore";
import authStore from "../../stores/authStore";
import MiniPlayer from "../MiniPlayer/component";
import instance from "../../axios/axios";
import { toJS } from "mobx";

import styles from "./Music.module.scss";
import UploadIcon from "../Home/components/UploadIcon";

const Music = observer(() => {
  const navigate = useNavigate();
  const [src, setSrc] = useState("");
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [trackName, setTrackName] = useState("");
  const [author, setAuthor] = useState("");
  const [activeTrackId, setActiveTrackId] = useState(null);

  const likedTracks = toJS(homeStore.likedTracks) || [];
  const isLoading = homeStore.isLoading;
  const error = homeStore.error;
  const user = authStore.user;
  const isArtist = authStore.isArtist;

  useEffect(() => {
    // Проверяем, авторизован ли пользователь
    if (!authStore.isAuthenticated) {
      console.log("Пользователь не авторизован, перенаправляем на /auth");
      navigate("/auth");
      return;
    }

    console.log("Начинаем загрузку лайкнутых треков");
    // Загружаем лайкнутые треки
    homeStore
      .fetchLikedTracks()
      .then((tracks) => {
        console.log(`Получено ${tracks.length} лайкнутых треков`);
      })
      .catch((error) => {
        console.error("Ошибка при загрузке лайкнутых треков:", error);
      });
  }, [navigate]);

  // Обработчик лайка/анлайка трека
  const handleLikeTrack = async (e, trackId) => {
    e.stopPropagation();

    try {
      console.log(`Вызываем unlike для трека с ID: ${trackId}`);
      // Для страницы "Моя музыка" это всегда будет анлайк (удаление из избранного)
      await homeStore.unlikeTrack(trackId);
      console.log("Успешно удален лайк");
    } catch (error) {
      console.error("Ошибка при удалении из избранного:", error);
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
    if (likedTracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex > 0 ? currentTrackIndex - 1 : likedTracks.length - 1;

    handlePlayAPITrack(likedTracks[newIndex], newIndex);
  };

  const handleNextTrack = () => {
    if (likedTracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex < likedTracks.length - 1 ? currentTrackIndex + 1 : 0;

    handlePlayAPITrack(likedTracks[newIndex], newIndex);
  };

  // Обработчик клика по профилю пользователя
  const handleProfileClick = () => {
    navigate("/settings");
  };

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
            <Link to="/music" className={styles.navLink + " " + styles.active}>
              <span className={styles.navIcon}>🎵</span>
              <span>Моя музыка</span>
            </Link>
            <Link to="/playlists" className={styles.navLink}>
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
            {/* Секция: Избранные треки */}
            <section className={styles.section}>
              <h2>Избранные треки</h2>
              {isLoading ? (
                <div className={styles.loading}>Загрузка...</div>
              ) : error ? (
                <div className={styles.error}>{error}</div>
              ) : (
                <div className={styles.trackList}>
                  {likedTracks.length > 0 ? (
                    likedTracks.map((track, index) => (
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
                            {track.artist?.user?.username ||
                              track.artist?.email ||
                              "Неизвестный исполнитель"}
                            {track.album && (
                              <>
                                <span className={styles.albumSeparator}>
                                  {" "}
                                  ·{" "}
                                </span>
                                <Link
                                  to={`/album/${track.album.id}`}
                                  className={styles.albumLink}
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {track.album.title}
                                </Link>
                              </>
                            )}
                          </div>
                        </div>
                        <div className={styles.trackDuration}>
                          {Math.floor(track.duration / 60)}:
                          {String(track.duration % 60).padStart(2, "0")}
                          <div
                            className={styles.trackLike}
                            onClick={(e) => handleLikeTrack(e, track.id)}
                          >
                            <span className={styles.likedIcon}>❤️</span>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className={styles.emptyState}>
                      У вас пока нет избранных треков
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

export default Music;
