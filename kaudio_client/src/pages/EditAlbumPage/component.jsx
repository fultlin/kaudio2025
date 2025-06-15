import { observer } from "mobx-react-lite";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import instance from "../../axios/axios";
import styles from "./EditAlbumPage.module.scss";
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

const EditAlbumPage = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [artists, setArtists] = useState([]);
  const [formData, setFormData] = useState({
    title: "",
    release_date: "",
    img_url: "",
    description: "",
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
        // Загружаем данные альбома
        const albumResponse = await instance.get(`albums/${id}/`);
        setAlbum(albumResponse.data);
        setFormData({
          title: albumResponse.data.title,
          release_date: albumResponse.data.release_date?.split("T")[0] || "",
          img_url: albumResponse.data.img_url || "",
          description: albumResponse.data.description || "",
          artist_id: albumResponse.data.artist?.id || "",
        });
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
      await instance.put(`albums/${id}/`, formData);
      const from = location.state?.from;
      navigate(from || `/albums/${id}`);
    } catch (err) {
      setError("Не удалось обновить альбом");
      console.error("Ошибка при обновлении альбома:", err);
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

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!album) {
    return <div className={styles.error}>Альбом не найден</div>;
  }

  // Формируем опции для селекта
  const artistOptions = artists.map((artist) => ({
    value: artist.id,
    label: artist.user?.username || artist.email,
  }));

  return (
    <div className={styles.editAlbumPage}>
      <h1>Редактирование альбома</h1>
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
          <label htmlFor="release_date">Дата выпуска</label>
          <input
            type="date"
            id="release_date"
            name="release_date"
            value={formData.release_date}
            onChange={handleChange}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="description">Описание</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
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

        <div className={styles.buttonGroup}>
          <button type="submit" className={styles.submitButton}>
            Сохранить
          </button>
          <button
            type="button"
            onClick={() => navigate(`/albums/${id}`)}
            className={styles.cancelButton}
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
});

export default EditAlbumPage;
