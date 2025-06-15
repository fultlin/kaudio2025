import { observer } from "mobx-react-lite";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import instance from "../../axios/axios";
import styles from "./EditTrackPage.module.scss";
import authStore from "../../stores/authStore";
import Select from "react-select";

const darkSelectStyles = {
  control: (provided, state) => ({
    ...provided,
    backgroundColor: "#181818",
    borderColor: state.isFocused ? "#900066" : "#333",
    color: "#fff",
    boxShadow: state.isFocused ? "0 0 0 2px rgba(144,0,102,0.2)" : undefined,
    minHeight: "44px",
  }),
  menu: (provided) => ({
    ...provided,
    backgroundColor: "#181818",
    color: "#fff",
    zIndex: 10,
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? "#900066"
      : state.isFocused
      ? "#333"
      : "#181818",
    color: "#fff",
    cursor: "pointer",
  }),
  singleValue: (provided) => ({
    ...provided,
    color: "#fff",
  }),
  input: (provided) => ({
    ...provided,
    color: "#fff",
  }),
  placeholder: (provided) => ({
    ...provided,
    color: "#aaa",
  }),
  dropdownIndicator: (provided) => ({
    ...provided,
    color: "#fff",
  }),
};

const EditTrackPage = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [track, setTrack] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [albums, setAlbums] = useState([]);
  const [artists, setArtists] = useState([]);
  const [formData, setFormData] = useState({
    title: "",
    duration: "",
    lyrics: "",
    img_url: "",
    audio_url: "",
    position: "",
    album_id: "",
    artist_id: "",
  });
  const { user } = authStore;

  useEffect(() => {
    if (user?.role !== "admin") {
      navigate("/");
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        // Загружаем данные трека
        const trackResponse = await instance.get(`tracks/${id}/`);
        setTrack(trackResponse.data);
        setFormData({
          title: trackResponse.data.title,
          duration: trackResponse.data.duration,
          lyrics: trackResponse.data.lyrics || "",
          img_url: trackResponse.data.img_url || "",
          audio_url: trackResponse.data.audio_url || "",
          position: trackResponse.data.position,
          album_id: trackResponse.data.album?.id || "",
          artist_id: trackResponse.data.artist?.id || "",
        });

        // Загружаем список альбомов
        const albumsResponse = await instance.get("albums/");
        setAlbums(albumsResponse.data);

        // Загружаем список исполнителей
        const artistsResponse = await instance.get("artists/");
        setArtists(artistsResponse.data);

        setError(null);
      } catch (err) {
        setError("Не удалось загрузить данные");
        console.error("Ошибка при загрузке данных:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await instance.put(`tracks/${id}/`, formData);
      const from = location.state?.from;
      navigate(from || `/tracks/${id}`);
    } catch (err) {
      setError("Не удалось обновить трек");
      console.error("Ошибка при обновлении трека:", err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Для react-select
  const handleArtistChange = (selected) => {
    setFormData((prev) => ({
      ...prev,
      artist_id: selected ? selected.value : "",
    }));
  };
  const handleAlbumChange = (selected) => {
    setFormData((prev) => ({
      ...prev,
      album_id: selected ? selected.value : "",
    }));
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!track) {
    return <div className={styles.error}>Трек не найден</div>;
  }

  // Формируем опции для селектов
  const artistOptions = artists.map((artist) => ({
    value: artist.id,
    label: artist.user?.username || artist.email,
  }));
  const albumOptions = albums.map((album) => ({
    value: album.id,
    label: album.title,
  }));

  return (
    <div className={styles.editTrackPage}>
      <h1>Редактирование трека</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label htmlFor="title">Название</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
          />
        </div>

        <div className={styles.formGroup}>
          <label>Исполнитель</label>
          <Select
            value={
              artistOptions.find((opt) => opt.value === formData.artist_id) ||
              null
            }
            onChange={handleArtistChange}
            options={artistOptions}
            placeholder="Выберите исполнителя"
            isClearable
            styles={darkSelectStyles}
          />
        </div>

        <div className={styles.formGroup}>
          <label>Альбом</label>
          <Select
            value={
              albumOptions.find((opt) => opt.value === formData.album_id) ||
              null
            }
            onChange={handleAlbumChange}
            options={albumOptions}
            placeholder="Выберите альбом"
            isClearable
            styles={darkSelectStyles}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="duration">Длительность (в секундах)</label>
          <input
            type="number"
            id="duration"
            name="duration"
            value={formData.duration}
            onChange={handleChange}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="position">Позиция в альбоме</label>
          <input
            type="number"
            id="position"
            name="position"
            value={formData.position}
            onChange={handleChange}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="lyrics">Текст песни</label>
          <textarea
            id="lyrics"
            name="lyrics"
            value={formData.lyrics}
            onChange={handleChange}
            rows="10"
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="img_url">URL обложки</label>
          <input
            type="url"
            id="img_url"
            name="img_url"
            value={formData.img_url}
            onChange={handleChange}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="audio_url">URL аудио</label>
          <input
            type="url"
            id="audio_url"
            name="audio_url"
            value={formData.audio_url}
            onChange={handleChange}
          />
        </div>

        <div className={styles.buttonGroup}>
          <button type="submit" className={styles.submitButton}>
            Сохранить
          </button>
          <button
            type="button"
            onClick={() => navigate(`/tracks/${id}`)}
            className={styles.cancelButton}
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
});

export default EditTrackPage;
