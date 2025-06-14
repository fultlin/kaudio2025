import { observer } from "mobx-react-lite";
import Reviews from "../../components/Reviews/component";
import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import instance from "../../axios/axios";
import styles from "./TrackPage.module.scss";
import { Link } from "react-router-dom";

const TrackPage = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [track, setTrack] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTrack = async () => {
      try {
        setLoading(true);
        const response = await instance.get(`tracks/${id}/`);
        setTrack(response.data);
        setError(null);
      } catch (err) {
        setError("Не удалось загрузить информацию о треке");
        console.error("Ошибка при загрузке трека:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrack();
  }, [id]);

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!track) {
    return <div className={styles.error}>Трек не найден</div>;
  }

  return (
    <div className={styles.trackPage}>
      <div className={styles.trackInfo}>
        <div className={styles.trackHeader}>
          <div className={styles.trackCover}>
            {track.cover_image ? (
              <img src={track.cover_image} alt={track.title} />
            ) : (
              <div className={styles.noCover}>Нет обложки</div>
            )}
          </div>
          <div className={styles.trackDetails}>
            <h1 className={styles.trackTitle}>{track.title}</h1>
            {track.artist && (
              <Link
                to={`/artist/${track.artist.id}`}
                className={styles.artistLink}
              >
                {track.artist.user?.username ||
                  track.artist.email ||
                  "Неизвестный исполнитель"}
              </Link>
            )}
            {track.album && (
              <Link
                to={`/album/${track.album.id}`}
                className={styles.albumLink}
              >
                {track.album.title}
              </Link>
            )}
            <div className={styles.trackMeta}>
              <span className={styles.duration}>
                {Math.floor(track.duration / 60)}:
                {String(track.duration % 60).padStart(2, "0")}
              </span>
              <span className={styles.plays}>
                {track.play_count} прослушиваний
              </span>
            </div>
          </div>
        </div>
        {track.lyrics && (
          <div className={styles.lyrics}>
            <h2>Текст песни</h2>
            <pre>{track.lyrics}</pre>
          </div>
        )}
      </div>
      <Reviews type="tracks" id={id} />
    </div>
  );
});

export default TrackPage;
