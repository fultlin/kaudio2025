import { observer } from "mobx-react-lite";
import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import instance from "../../axios/axios";
import styles from "./EditAlbumPage.module.scss";
import authStore from "../../stores/authStore";

const EditAlbumPage = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    title: "",
    release_date: "",
    img_url: "",
    description: "",
  });
  const { user } = authStore;

  useEffect(() => {
    if (user?.role !== "admin") {
      navigate("/");
      return;
    }

    const fetchAlbum = async () => {
      try {
        setLoading(true);
        const response = await instance.get(`albums/${id}/`);
        setAlbum(response.data);
        setFormData({
          title: response.data.title,
          release_date: response.data.release_date.split("T")[0],
          img_url: response.data.img_url || "",
          description: response.data.description || "",
        });
        setError(null);
      } catch (err) {
        setError("Не удалось загрузить информацию об альбоме");
        console.error("Ошибка при загрузке альбома:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAlbum();
  }, [id, user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await instance.put(`albums/${id}/`, formData);
      navigate(`/albums/${id}`);
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
