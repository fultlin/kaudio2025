import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import instance from "../../axios/axios";
import styles from "./CreatePlaylist.module.scss";
import authStore from "../../stores/authStore";

const CreatePlaylist = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });
  const [error, setError] = useState("");
  const user = authStore.user;

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
      // Проверяем, что title не пустой
      if (!formData.title.trim()) {
        setError("Название плейлиста обязательно");
        return;
      }

      // Проверяем наличие пользователя
      if (!user || !user.id) {
        setError("Необходимо авторизоваться для создания плейлиста");
        return;
      }

      const response = await instance.post("playlists/", {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        is_public: true,
        user_id: user.id, // Добавляем ID пользователя
      });

      if (response.data && response.data.id) {
        navigate(`/playlists/${response.data.id}`);
      } else {
        throw new Error("Не удалось получить ID созданного плейлиста");
      }
    } catch (err) {
      console.error("Ошибка при создании плейлиста:", err);
      if (err.response?.data) {
        // Если есть детальная информация об ошибке от сервера
        const errorMessage = Object.values(err.response.data).flat().join(", ");
        setError(errorMessage || "Ошибка при создании плейлиста");
      } else {
        setError("Ошибка при создании плейлиста");
      }
    }
  };

  // Проверяем авторизацию при монтировании компонента
  React.useEffect(() => {
    if (!user) {
      navigate("/auth");
    }
  }, [user, navigate]);

  if (!user) {
    return null; // или можно показать сообщение о необходимости авторизации
  }

  return (
    <div className={styles.createPlaylist}>
      <h2>Создать новый плейлист</h2>
      {error && <div className={styles.error}>{error}</div>}
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formGroup}>
          <label htmlFor="title">Название плейлиста *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Введите название плейлиста"
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
            placeholder="Добавьте описание плейлиста (необязательно)"
          />
        </div>
        <div className={styles.buttons}>
          <button type="submit" className={styles.submitButton}>
            Создать плейлист
          </button>
          <button
            type="button"
            onClick={() => navigate("/playlists")}
            className={styles.cancelButton}
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreatePlaylist;
