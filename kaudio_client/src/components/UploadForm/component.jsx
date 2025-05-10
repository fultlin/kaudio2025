import React, { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import instance from "../../axios/axios";
import authStore from "../../stores/authStore";
import { useNavigate } from "react-router-dom";
import styles from "./UploadForm.module.scss";

const UploadForm = observer(() => {
  const [formData, setFormData] = useState({
    title: "",
    album_id: "",
    track_number: 1,
    duration: 0,
    genre_ids: [],
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [albums, setAlbums] = useState([]);
  const [genres, setGenres] = useState([]);
  const [artistId, setArtistId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Проверяем авторизацию
    if (!authStore.isAuthenticated) {
      setError("Необходимо авторизоваться для загрузки треков");
      return;
    }

    // Загружаем жанры и определяем ID исполнителя (текущего пользователя)
    const fetchData = async () => {
      try {
        // Получаем жанры
        const genresRes = await instance.get("genres/");
        setGenres(genresRes.data);

        // Находим или создаем запись исполнителя для текущего пользователя
        const userRes = await instance.get("users/me/");
        const userId = userRes.data.id;

        // Получаем исполнителя по email пользователя
        // Предполагается, что email пользователя совпадает с email исполнителя
        try {
          const artistsRes = await instance.get(
            `artists/?email=${userRes.data.email}`
          );
          if (artistsRes.data && artistsRes.data.length > 0) {
            // Исполнитель найден
            setArtistId(artistsRes.data[0].id);

            // Получаем альбомы этого исполнителя
            const albumsRes = await instance.get(
              `artists/${artistsRes.data[0].id}/albums/`
            );
            setAlbums(albumsRes.data);
          } else {
            // Исполнитель не найден, предлагаем создать
            setError(
              "Для вас не создан профиль исполнителя. Обратитесь к администратору."
            );
          }
        } catch (err) {
          console.error("Ошибка при поиске исполнителя:", err);
          setError("Не удалось найти ваш профиль исполнителя");
        }
      } catch (error) {
        console.error("Ошибка при загрузке данных:", error);
        setError("Не удалось загрузить данные");
      }
    };

    fetchData();
  }, []);

  // Обработчик изменения текстовых полей
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Обработчик изменения файла с автоматическим извлечением длительности
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);

    // Извлекаем длительность аудиофайла
    if (selectedFile && selectedFile.type.startsWith("audio/")) {
      const audioElement = document.createElement("audio");
      audioElement.src = URL.createObjectURL(selectedFile);

      // Когда метаданные загружены, получаем длительность
      audioElement.addEventListener("loadedmetadata", () => {
        const durationInSeconds = Math.round(audioElement.duration);
        setFormData((prev) => ({
          ...prev,
          duration: durationInSeconds,
        }));
        console.log(`Длительность трека: ${durationInSeconds} секунд`);
      });

      // Обработка ошибок при загрузке аудио
      audioElement.addEventListener("error", () => {
        console.error("Ошибка при загрузке аудиофайла");
        setError("Не удалось прочитать аудиофайл. Проверьте формат файла.");
      });
    } else {
      setError("Выбранный файл не является аудиофайлом");
    }
  };

  // Обработчик изменения жанров (множественный выбор)
  const handleGenreChange = (e) => {
    const options = e.target.options;
    const selectedGenres = [];

    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) {
        selectedGenres.push(options[i].value);
      }
    }

    setFormData((prev) => ({
      ...prev,
      genre_ids: selectedGenres,
    }));
  };

  // Отправка формы
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!authStore.isAuthenticated) {
      setError("Необходимо авторизоваться");
      return;
    }

    if (!artistId) {
      setError("Профиль исполнителя не найден");
      return;
    }

    if (!file) {
      setError("Выберите аудиофайл");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Создаем FormData для отправки файла
      const submitData = new FormData();
      submitData.append("audio_file", file);

      // Добавляем artistId автоматически
      submitData.append("artist_id", artistId);

      // Добавляем остальные поля
      Object.keys(formData).forEach((key) => {
        if (key === "genre_ids" && formData[key].length > 0) {
          // Для множественных полей
          formData[key].forEach((id) => {
            submitData.append("genre_ids", id);
          });
        } else {
          submitData.append(key, formData[key]);
        }
      });

      // Отправляем запрос
      const response = await instance.post("tracks/upload/", submitData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Трек успешно загружен:", response.data);

      // Перенаправляем на страницу трека
      navigate(`/tracks/${response.data.id}`);
    } catch (error) {
      console.error("Ошибка при загрузке трека:", error);
      setError(error.response?.data?.error || "Ошибка при загрузке трека");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.uploadContainer}>
      <h2>Загрузка нового трека</h2>

      {error && <div className={styles.error}>{error}</div>}

      <form onSubmit={handleSubmit} className={styles.uploadForm}>
        <div className={styles.formGroup}>
          <label htmlFor="title">Название трека:</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            className={styles.input}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="album_id">Альбом:</label>
          <select
            id="album_id"
            name="album_id"
            value={formData.album_id}
            onChange={handleChange}
            required
            disabled={!artistId}
            className={styles.select}
          >
            <option value="">Выберите альбом</option>
            {albums.map((album) => (
              <option key={album.id} value={album.id}>
                {album.title}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="track_number">Номер трека в альбоме:</label>
          <input
            type="number"
            id="track_number"
            name="track_number"
            value={formData.track_number}
            onChange={handleChange}
            min="1"
            required
            className={styles.input}
          />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="duration">
            Длительность (сек) - заполняется автоматически:
          </label>
          <input
            type="number"
            id="duration"
            name="duration"
            value={formData.duration}
            onChange={handleChange}
            min="1"
            required
            readOnly
            className={styles.input}
          />
          <small>
            Длительность определяется автоматически из загруженного файла
          </small>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="genre_ids">Жанры:</label>
          <select
            id="genre_ids"
            name="genre_ids"
            multiple
            value={formData.genre_ids}
            onChange={handleGenreChange}
            className={styles.selectMultiple}
          >
            {genres.map((genre) => (
              <option key={genre.id} value={genre.id}>
                {genre.title}
              </option>
            ))}
          </select>
          <small>Удерживайте Ctrl для выбора нескольких жанров</small>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="audio_file">Аудиофайл:</label>
          <input
            type="file"
            id="audio_file"
            accept="audio/*"
            onChange={handleFileChange}
            required
            className={styles.fileInput}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !artistId}
          className={styles.submitButton}
        >
          {loading ? "Загрузка..." : "Загрузить трек"}
        </button>
      </form>
    </div>
  );
});

export default UploadForm;
