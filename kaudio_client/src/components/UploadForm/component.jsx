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
  const [useAlbum, setUseAlbum] = useState(false); // По умолчанию не используем альбом
  const navigate = useNavigate();

  useEffect(() => {
    if (!authStore.isAuthenticated) {
      setError("Необходимо авторизоваться для загрузки треков");
      return;
    }

    const fetchData = async () => {
      try {
        const genresRes = await instance.get("genres/");
        setGenres(genresRes.data);

        const userRes = await instance.get("users/me/");
        const userId = userRes.data.id;

        try {
          const artistsRes = await instance.get(
            `artists/?user=${userRes.data.id}`
          );
          if (artistsRes.data && artistsRes.data.length > 0) {
            setArtistId(artistsRes.data[0].id);

            const albumsRes = await instance.get(
              `artists/${artistsRes.data[0].id}/albums/`
            );
            setAlbums(albumsRes.data);
          } else {
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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleUseAlbumChange = (e) => {
    setUseAlbum(e.target.checked);
    if (!e.target.checked) {
      setFormData((prev) => ({
        ...prev,
        album_id: "",
      }));
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);

    if (selectedFile && selectedFile.type.startsWith("audio/")) {
      const audioElement = document.createElement("audio");
      audioElement.src = URL.createObjectURL(selectedFile);

      audioElement.addEventListener("loadedmetadata", () => {
        const durationInSeconds = Math.round(audioElement.duration);
        setFormData((prev) => ({
          ...prev,
          duration: durationInSeconds,
        }));
        console.log(`Длительность трека: ${durationInSeconds} секунд`);
      });

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

    // Проверяем, выбран ли альбом, если используем альбом
    if (useAlbum && !formData.album_id) {
      setError("Выберите альбом");
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

      // Добавляем остальные поля, кроме album_id и track_number если не используем альбом
      Object.keys(formData).forEach((key) => {
        if (key === "genre_ids" && formData[key].length > 0) {
          // Для множественных полей
          formData[key].forEach((id) => {
            submitData.append("genre_ids", id);
          });
        } else if (
          (key === "album_id" || key === "track_number") &&
          !useAlbum
        ) {
          // Пропускаем album_id и track_number если не используем альбом
          return;
        } else {
          submitData.append(key, formData[key]);
        }
      });

      // Отправляем запрос
      const response = await instance.post("upload/track/", submitData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Трек успешно загружен:", response.data);

      // Перенаправляем на главную страницу
      navigate("/", {
        state: { message: "Трек успешно загружен" },
      });
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
          <div className={styles.checkboxContainer}>
            <input
              type="checkbox"
              id="useAlbum"
              checked={useAlbum}
              onChange={handleUseAlbumChange}
              className={styles.checkbox}
            />
            <label htmlFor="useAlbum" className={styles.checkboxLabel}>
              Добавить в существующий альбом
            </label>
          </div>
          <small className={styles.helperText}>
            {useAlbum
              ? "Трек будет добавлен в выбранный альбом"
              : "Трек будет загружен без привязки к альбому"}
          </small>
        </div>

        {useAlbum && (
          <>
            <div className={styles.formGroup}>
              <label htmlFor="album_id">Альбом:</label>
              <select
                id="album_id"
                name="album_id"
                value={formData.album_id}
                onChange={handleChange}
                required={useAlbum}
                disabled={!artistId || !useAlbum}
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
                required={useAlbum}
                disabled={!useAlbum}
                className={styles.input}
              />
            </div>
          </>
        )}

        <div className={styles.formGroup}>
          <label htmlFor="duration" id="duration-label">
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
            aria-labelledby="duration-label"
            aria-readonly="true"
          />
          <small id="duration-help" className={styles.helpText}>
            Длительность определяется автоматически из загруженного файла
          </small>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="genre_ids" id="genres-label">
            Жанры:
          </label>
          <select
            id="genre_ids"
            name="genre_ids"
            multiple
            value={formData.genre_ids}
            onChange={handleGenreChange}
            className={styles.selectMultiple}
            aria-labelledby="genres-label"
            aria-describedby="genres-help"
          >
            {genres.map((genre) => (
              <option key={genre.id} value={genre.id}>
                {genre.title}
              </option>
            ))}
          </select>
          <small id="genres-help" className={styles.helpText}>
            Удерживайте Ctrl для выбора нескольких жанров
          </small>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="audio_file" id="file-label">
            Аудиофайл:
          </label>
          <input
            type="file"
            id="audio_file"
            accept="audio/*"
            onChange={handleFileChange}
            required
            className={styles.fileInput}
            aria-labelledby="file-label"
            aria-required="true"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !artistId || (useAlbum && !formData.album_id)}
          className={styles.submitButton}
          aria-disabled={
            loading || !artistId || (useAlbum && !formData.album_id)
          }
        >
          {loading ? "Загрузка..." : "Загрузить трек"}
        </button>
      </form>
    </div>
  );
});

export default UploadForm;
