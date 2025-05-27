import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import instance from "../../axios/axios";
import styles from "./EditPlaylist.module.scss";

const EditPlaylist = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlaylist = async () => {
      try {
        const response = await instance.get(`/playlists/${id}/`);
        setFormData({
          title: response.data.title,
          description: response.data.description || "",
        });
        setLoading(false);
      } catch (err) {
        setError("Ошибка при загрузке плейлиста");
        setLoading(false);
        console.error("Ошибка:", err);
      }
    };

    fetchPlaylist();
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await instance.put(`/playlists/${id}/`, formData);
      navigate(`/playlists/${id}`);
    } catch (err) {
      setError("Ошибка при обновлении плейлиста");
      console.error("Ошибка:", err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm("Вы уверены, что хотите удалить этот плейлист?")) {
      try {
        await instance.delete(`/playlists/${id}/`);
        navigate("/playlists");
      } catch (err) {
        setError("Ошибка при удалении плейлиста");
        console.error("Ошибка:", err);
      }
    }
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  return (
    <div className={styles.editPlaylist}>
      <h2>Редактировать плейлист</h2>
      {error && <div className={styles.error}>{error}</div>}
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label htmlFor="title">Название плейлиста</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
          />
        </div>
        <div className={styles.formGroup}>
          <label htmlFor="description">Описание</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="4"
          />
        </div>
        <div className={styles.buttons}>
          <button type="submit" className={styles.submitButton}>
            Сохранить изменения
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className={styles.deleteButton}
          >
            Удалить плейлист
          </button>
          <button
            type="button"
            onClick={() => navigate(`/playlists/${id}`)}
            className={styles.cancelButton}
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditPlaylist;
