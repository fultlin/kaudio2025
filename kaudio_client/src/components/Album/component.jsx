import { observer } from "mobx-react-lite";
import { useEffect, useState } from "react";
import { useParams, useNavigate, Link, useLocation } from "react-router-dom";
import homeStore from "../../stores/homeStore";
import authStore from "../../stores/authStore";
import instance from "../../axios/axios";
import { toJS } from "mobx";
import styles from "./Album.module.scss";
import { ArrowRight } from "lucide-react";

const Album = observer((props) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAdmin } = authStore;

  const [album, setAlbum] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [trackLikes, setTrackLikes] = useState({});
  const [isAlbumLiked, setIsAlbumLiked] = useState(false);

  // Используем props или локальное состояние
  const setTrackName = props.setTrackName || (() => {});
  const setAuthor = props.setAuthor || (() => {});
  const setSrc = props.setSrc || (() => {});
  const setIsPlaying = props.setIsPlaying || (() => {});
  const setActiveTrackId = props.setActiveTrackId || (() => {});
  const setCurrentTrackIndex = props.setCurrentTrackIndex || (() => {});
  const setTracks = props.setTracks || (() => {});

  const isPlaying = props.isPlaying !== undefined ? props.isPlaying : false;
  const activeTrackId = props.activeTrackId;
  const tracks = props.tracks || [];

  useEffect(() => {
    // Проверяем, авторизован ли пользователь
    if (!authStore.isAuthenticated) {
      console.log("Пользователь не авторизован, перенаправляем на /auth");
      navigate("/auth");
      return;
    }

    // Загружаем данные альбома и его треки
    const fetchAlbumData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Получаем данные альбома
        const albumData = await homeStore.fetchAlbumById(id);
        if (!albumData) {
          setError("Альбом не найден");
          setIsLoading(false);
          return;
        }

        setAlbum(albumData);

        // Проверяем, лайкнут ли альбом
        const albumLiked = await homeStore.isAlbumLiked(parseInt(id));
        setIsAlbumLiked(albumLiked);

        // Получаем треки альбома
        let albumTracks = [];
        if (Array.isArray(albumData.tracks) && albumData.tracks.length > 0) {
          albumTracks = albumData.tracks;
        } else {
          // Делаем отдельный запрос на /tracks/?album_id={id}
          try {
            const response = await instance.get(`tracks/?album_id=${id}`);
            // Фильтруем только треки этого альбома
            albumTracks = Array.isArray(response.data)
              ? response.data.filter(
                  (track) =>
                    track.album &&
                    (track.album.id === Number(id) ||
                      track.album === Number(id))
                )
              : [];
          } catch (err) {
            console.error("Ошибка при загрузке треков альбома:", err);
            albumTracks = [];
          }
        }
        setTracks(albumTracks);

        // Для каждого трека определяем, лайкнут ли он
        const likesMap = {};
        for (const track of albumTracks) {
          likesMap[track.id] = await homeStore.isTrackLiked(track.id);
        }
        setTrackLikes(likesMap);
      } catch (err) {
        console.error("Ошибка при загрузке данных альбома:", err);
        setError("Ошибка при загрузке альбома и его треков");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAlbumData();
  }, [id, navigate, setTracks]);

  // Обработчик лайка/анлайка трека
  const handleLikeTrack = async (e, trackId) => {
    e.stopPropagation();

    try {
      if (trackLikes[trackId]) {
        // Если трек уже лайкнут, удаляем лайк
        console.log(`Удаляем лайк у трека с ID: ${trackId}`);
        await homeStore.unlikeTrack(trackId);
        setTrackLikes((prev) => ({ ...prev, [trackId]: false }));
      } else {
        // Если трек не лайкнут, добавляем лайк
        console.log(`Добавляем лайк треку с ID: ${trackId}`);
        await homeStore.likeTrack(trackId);
        setTrackLikes((prev) => ({ ...prev, [trackId]: true }));
      }
    } catch (error) {
      console.error("Ошибка при обновлении лайка трека:", error);
    }
  };

  // Обработчик лайка/анлайка альбома
  const handleLikeAlbum = async (e) => {
    e.stopPropagation();

    try {
      if (isAlbumLiked) {
        // Если альбом уже лайкнут, удаляем лайк
        console.log(`Удаляем лайк у альбома с ID: ${id}`);
        await homeStore.unlikeAlbum(id);
        setIsAlbumLiked(false);
      } else {
        // Если альбом не лайкнут, добавляем лайк
        console.log(`Добавляем лайк альбому с ID: ${id}`);
        await homeStore.likeAlbum(id);
        setIsAlbumLiked(true);
      }
    } catch (error) {
      console.error("Ошибка при обновлении лайка альбома:", error);
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

  // Воспроизведение всего альбома, начиная с первого трека
  const handlePlayAlbum = () => {
    if (tracks.length > 0) {
      handlePlayAPITrack(tracks[0], 0);
    }
  };

  // Форматирование времени в минуты:секунды
  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
  };

  if (isLoading) {
    return <div className={styles.loading}>Загрузка альбома...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!album) {
    return <div className={styles.error}>Альбом не найден</div>;
  }

  return (
    <div className={styles.albumContainer} role="main" id="main-content">
      <div className={styles.albumHeader}>
        <div
          className={styles.albumCover}
          role="img"
          aria-label={`Обложка альбома ${album.title}`}
        >
          {album.img_url ? (
            <img src={album.img_url} alt={`Обложка альбома ${album.title}`} />
          ) : (
            <div className={styles.noImage} aria-hidden="true"></div>
          )}
        </div>

        <div className={styles.albumInfo}>
          <div className={styles.albumType} aria-label="Тип контента">
            Альбом
          </div>
          <h1 className={styles.albumTitle}>{album.title}</h1>

          <div className={styles.albumMeta} role="contentinfo">
            {album.artist && (
              <Link
                to={`/artist/${album.artist.id}`}
                className={styles.artistLink}
                onClick={(e) => e.stopPropagation()}
                aria-label={`Перейти на страницу исполнителя ${
                  album.artist.user?.username || "Неизвестный исполнитель"
                }`}
              >
                {album.artist.img_cover_url && (
                  <div className={styles.artistImage}>
                    <img
                      src={album.artist.img_cover_url}
                      alt=""
                      aria-hidden="true"
                    />
                  </div>
                )}
                <span>
                  {album.artist.user?.username || "Неизвестный исполнитель"}
                </span>
              </Link>
            )}

            <span className={styles.dot} aria-hidden="true">
              •
            </span>
            <span className={styles.releaseYear}>
              {new Date(album.release_date).getFullYear()}
            </span>

            <span className={styles.dot} aria-hidden="true">
              •
            </span>
            <span className={styles.songCount}>
              {album.total_tracks}{" "}
              {album.total_tracks === 1
                ? "трек"
                : album.total_tracks > 1 && album.total_tracks < 5
                ? "трека"
                : "треков"}
            </span>
          </div>

          <div className={styles.albumControls}>
            <button
              onClick={handlePlayAlbum}
              className={styles.playButton}
              aria-label={`${
                isPlaying ? "Остановить" : "Воспроизвести"
              } альбом ${album.title}`}
            >
              <span className={styles.playIcon} aria-hidden="true">
                ▶
              </span>
            </button>

            <button
              className={styles.albumLike}
              onClick={handleLikeAlbum}
              aria-label={`${
                isAlbumLiked ? "Удалить из избранного" : "Добавить в избранное"
              } альбом ${album.title}`}
              aria-pressed={isAlbumLiked}
            >
              {isAlbumLiked ? (
                <span className={styles.likedIcon} aria-hidden="true">
                  ❤️
                </span>
              ) : (
                <span className={styles.unlikedIcon} aria-hidden="true">
                  🤍
                </span>
              )}
            </button>

            {isAdmin && (
              <button
                className={styles.editButton}
                onClick={() =>
                  navigate(`/albums/${album.id}/edit`, {
                    state: { from: location.pathname },
                  })
                }
                style={{ marginLeft: 16 }}
              >
                Редактировать
              </button>
            )}
          </div>
        </div>
      </div>

      <div
        className={styles.trackList}
        role="region"
        aria-label="Список треков"
      >
        <div className={styles.trackListHeader} role="row">
          <div className={styles.trackNumberHeader} role="columnheader">
            #
          </div>
          <div role="columnheader" aria-hidden="true"></div>
          <div className={styles.trackTitleHeader} role="columnheader">
            Название
          </div>
          <div className={styles.trackDurationHeader} role="columnheader">
            Длительность
          </div>
        </div>

        {tracks.length === 0 ? (
          <div className={styles.error} style={{ margin: 24 }}>
            В этом альбоме пока нет треков
          </div>
        ) : (
          tracks.map((track, index) => (
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
                  {track.artist?.user?.username || "Неизвестный исполнитель"}
                </div>
              </div>
              <div className={styles.trackDuration}>
                {formatDuration(track.duration)}
                <div
                  className={styles.trackLike}
                  onClick={(e) => handleLikeTrack(e, track.id)}
                >
                  {trackLikes[track.id] ? (
                    <span className={styles.likedIcon}>❤️</span>
                  ) : (
                    <span className={styles.unlikedIcon}>🤍</span>
                  )}
                </div>
              </div>
              <div
                className={styles.trackGoTo}
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/tracks/${track.id}`, {
                    state: { from: location.pathname },
                  });
                }}
                title="Перейти на страницу трека"
              >
                <ArrowRight size={20} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
});

export default Album;
