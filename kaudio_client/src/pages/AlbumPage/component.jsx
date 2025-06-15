import { observer } from "mobx-react-lite";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import instance from "../../axios/axios";
import styles from "./AlbumPage.module.scss";
import Reviews from "../../components/Reviews/component";
import authStore from "../../stores/authStore";

const AlbumPage = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user, isAdmin } = authStore;

  useEffect(() => {
    const fetchAlbum = async () => {
      try {
        setLoading(true);
        const response = await instance.get(`albums/${id}/`);
        setAlbum(response.data);
        setError(null);
      } catch (err) {
        setError("Не удалось загрузить информацию об альбоме");
        console.error("Ошибка при загрузке альбома:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAlbum();
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm("Вы уверены, что хотите удалить этот альбом?")) {
      try {
        await instance.delete(`albums/${id}/`);
        navigate("/albums");
      } catch (err) {
        setError("Не удалось удалить альбом");
        console.error("Ошибка при удалении альбома:", err);
      }
    }
  };

  const handleEdit = () => {
    navigate(`/albums/${id}/edit`);
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!album) {
    return <div className={styles.error}>Альбом не найден</div>;
  }

  return (
    <div className={styles.albumPage}>
      <div className={styles.albumInfo}>
        <div className={styles.albumHeader}>
          <div className={styles.albumCover}>
            {album.img_url ? (
              <img src={album.img_url} alt={album.title} />
            ) : (
              <div className={styles.noCover}>Нет обложки</div>
            )}
          </div>
          <div className={styles.albumDetails}>
            <h1 className={styles.albumTitle}>{album.title}</h1>
            {album.artist && (
              <Link
                to={`/artist/${album.artist.id}`}
                className={styles.artistLink}
              >
                {album.artist.user?.username ||
                  album.artist.email ||
                  "Неизвестный исполнитель"}
              </Link>
            )}
            <div className={styles.albumMeta}>
              <span className={styles.releaseYear}>
                {new Date(album.release_date).getFullYear()}
              </span>
              <span className={styles.trackCount}>
                {album.total_tracks} треков
              </span>
              <span className={styles.duration}>
                {Math.floor(album.total_duration / 60)}:
                {String(album.total_duration % 60).padStart(2, "0")}
              </span>
            </div>
            {isAdmin && (
              <div className={styles.adminControls}>
                <button onClick={handleEdit} className={styles.editButton}>
                  Редактировать
                </button>
                <button onClick={handleDelete} className={styles.deleteButton}>
                  Удалить
                </button>
              </div>
            )}
          </div>
        </div>

        <div className={styles.tracksList}>
          <h2>Треки</h2>
          {album.tracks?.map((track) => (
            <div key={track.id} className={styles.trackItem}>
              <Link to={`/tracks/${track.id}`} className={styles.trackLink}>
                <span className={styles.trackNumber}>{track.position}</span>
                <span className={styles.trackTitle}>{track.title}</span>
                <span className={styles.trackDuration}>
                  {Math.floor(track.duration / 60)}:
                  {String(track.duration % 60).padStart(2, "0")}
                </span>
              </Link>
            </div>
          ))}
        </div>
      </div>
      <Reviews type="albums" id={id} />
    </div>
  );
});

export default AlbumPage;
