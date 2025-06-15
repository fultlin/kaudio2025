import React, { useState, useRef, useEffect } from "react";
import { observer } from "mobx-react-lite";
import { useNavigate } from "react-router-dom";
import authStore from "../../stores/authStore";
import instance from "../../axios/axios";
import { getFullImageUrl } from "../../utils/imageUtils";
import styles from "./UploadTrack.module.scss";

const UploadTrack = observer(() => {
  const [formData, setFormData] = useState({
    title: "",
    duration: 0,
    genre_ids: [],
  });

  const [audioFile, setAudioFile] = useState(null);
  const [coverImage, setCoverImage] = useState(null);
  const [coverImagePreview, setCoverImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);
  const [success, setSuccess] = useState(null);
  const [genres, setGenres] = useState([]);
  const [createAlbum, setCreateAlbum] = useState(true); // По умолчанию создаем альбом для трека

  const audioFileInputRef = useRef(null);
  const coverImageInputRef = useRef(null);

  const navigate = useNavigate();

  useEffect(() => {
    // Проверяем авторизацию и статус исполнителя
    if (!authStore.isAuthenticated) {
      navigate("/auth");
      return;
    }

    if (!authStore.isArtist) {
      navigate("/settings");
      return;
    }

    // Загружаем список жанров
    const fetchGenres = async () => {
      try {
        const response = await instance.get("genres/");
        setGenres(response.data);
      } catch (error) {
        console.error("Ошибка при загрузке жанров:", error);
        setError("Не удалось загрузить список жанров");
      }
    };

    fetchGenres();
  }, [navigate]);

  // Обработчик изменения текстовых полей
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Обработчик переключателя создания альбома
  const handleCreateAlbumChange = (e) => {
    setCreateAlbum(e.target.checked);
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

  // Обработчик выбора аудиофайла
  const handleAudioFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith("audio/")) {
      setError("Пожалуйста, выберите аудиофайл");
      return;
    }

    setAudioFile(file);

    // Извлекаем длительность аудиофайла
    const audio = document.createElement("audio");
    audio.src = URL.createObjectURL(file);

    audio.onloadedmetadata = () => {
      const durationInSeconds = Math.round(audio.duration);
      setFormData((prev) => ({
        ...prev,
        duration: durationInSeconds,
      }));
    };

    audio.onerror = () => {
      setError("Не удалось прочитать аудиофайл");
    };
  };

  // Обработчик выбора обложки
  const handleCoverImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Пожалуйста, выберите изображение");
      return;
    }

    setCoverImage(file);

    // Создаем превью
    const preview = URL.createObjectURL(file);
    setCoverImagePreview(preview);
  };

  // Отправка формы
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      let albumId = null;
      let coverUrl = null;

      // Если выбрано создание альбома, сначала создаем его
      if (createAlbum) {
        const albumFormData = new FormData();
        albumFormData.append("title", formData.title);
        albumFormData.append("description", `Сингл: ${formData.title}`);
        albumFormData.append("artist_id", authStore.artistProfile.id);

        // Если есть обложка, загружаем её
        if (coverImage) {
          albumFormData.append("cover_image", coverImage);
        }

        const albumResponse = await instance.post(
          "upload/album/",
          albumFormData
        );
        albumId = albumResponse.data.id;
        coverUrl = albumResponse.data.cover_image;
      }

      // Затем загружаем трек
      const trackFormData = new FormData();
      trackFormData.append("audio_file", audioFile);
      trackFormData.append("title", formData.title);
      trackFormData.append("artist_id", authStore.artistProfile.id);
      trackFormData.append("duration", formData.duration);

      // Добавляем идентификатор альбома только если он был создан
      if (albumId) {
        trackFormData.append("album_id", albumId);
        trackFormData.append("track_number", 1); // Номер трека в альбоме
      }

      // Если есть обложка, добавляем URL
      if (coverUrl) {
        trackFormData.append("img_url", coverUrl);
      } else {
        trackFormData.append("img_url", ""); // Пустая строка, если обложки нет
      }

      // Добавляем жанры
      formData.genre_ids.forEach((genreId) => {
        trackFormData.append("genre_ids", genreId);
      });

      // Отладочная информация
      console.log("Отправляем данные трека:", {
        title: formData.title,
        artist_id: authStore.artistProfile.id,
        duration: formData.duration,
        album_id: albumId,
        track_number: albumId ? 1 : null,
        img_url: coverUrl || "",
        genre_ids: formData.genre_ids,
      });

      // Отправляем данные
      const response = await instance.post("upload/track/", trackFormData);

      setSuccess("Трек успешно загружен!");

      // Очищаем форму
      setFormData({
        title: "",
        duration: 0,
        genre_ids: [],
      });
      setAudioFile(null);
      setCoverImage(null);
      if (coverImagePreview) URL.revokeObjectURL(coverImagePreview);
      setCoverImagePreview(null);

      // Перенаправляем на страницу трека
      setTimeout(() => {
        navigate(`/tracks/${response.data.id}`);
      }, 1500);
    } catch (error) {
      console.error("Ошибка при загрузке трека:", error);
      console.log("Детали ошибки:", error.response?.data);

      // Обработка различных типов ошибок
      if (
        error.response?.status === 500 &&
        error.response?.data?.includes("UNIQUE constraint failed")
      ) {
        setError(
          "Трек с таким названием уже существует в этом альбоме. Пожалуйста, выберите другое название."
        );
        setErrorType("unique");
      } else if (error.response?.data?.title) {
        setError(`Ошибка: ${error.response.data.title.join(", ")}`);
        setErrorType(null);
      } else if (error.response?.data?.detail) {
        setError(`Ошибка: ${error.response.data.detail}`);
        setErrorType(null);
      } else if (error.response?.data?.error) {
        setError(`Ошибка: ${error.response.data.error}`);
        setErrorType(null);
      } else {
        setError("Не удалось загрузить трек. Пожалуйста, попробуйте еще раз.");
        setErrorType(null);
      }
    } finally {
      setLoading(false);
    }
  };

  // Очищаем URL при размонтировании
  useEffect(() => {
    return () => {
      if (coverImagePreview) URL.revokeObjectURL(coverImagePreview);
    };
  }, [coverImagePreview]);

  return (
    <div className={styles.uploadContainer}>
      <h1 className={styles.title}>Загрузка трека</h1>

      {error && (
        <div className={styles.error} data-type={errorType}>
          {error}
        </div>
      )}
      {success && <div className={styles.success}>{success}</div>}

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
            placeholder="Введите название трека"
          />
        </div>

        <div className={styles.formGroup}>
          <div className={styles.checkboxContainer}>
            <input
              type="checkbox"
              id="createAlbum"
              checked={createAlbum}
              onChange={handleCreateAlbumChange}
              className={styles.checkbox}
            />
            <label htmlFor="createAlbum" className={styles.checkboxLabel}>
              Создать альбом для этого трека
            </label>
          </div>
          <small className={styles.helperText}>
            {createAlbum
              ? "Трек будет добавлен в новый альбом-сингл"
              : "Трек будет загружен без привязки к альбому"}
          </small>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label htmlFor="audioFile">Аудиофайл:</label>
            <div className={styles.fileInputWrapper}>
              <input
                type="file"
                id="audioFile"
                accept="audio/*"
                ref={audioFileInputRef}
                onChange={handleAudioFileChange}
                required
                className={styles.fileInput}
              />
              <label htmlFor="audioFile" className={styles.fileInputLabel}>
                {audioFile ? audioFile.name : "Выберите аудиофайл"}
              </label>
            </div>
            {formData.duration > 0 && (
              <div className={styles.durationInfo}>
                Длительность: {Math.floor(formData.duration / 60)}:
                {String(formData.duration % 60).padStart(2, "0")}
              </div>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="coverImage">Обложка трека:</label>
            <div className={styles.imageUploadContainer}>
              <div className={styles.imagePreviewWrapper}>
                {coverImagePreview ? (
                  <img
                    src={coverImagePreview}
                    alt="Обложка трека"
                    className={styles.previewImg}
                  />
                ) : (
                  <div className={styles.imagePlaceholder}>
                    <span>Обложка</span>
                  </div>
                )}
              </div>
              <div className={styles.imageControls}>
                <input
                  type="file"
                  id="coverImage"
                  accept="image/*"
                  ref={coverImageInputRef}
                  onChange={handleCoverImageChange}
                  className={styles.fileInput}
                />
                <label htmlFor="coverImage" className={styles.uploadButton}>
                  Выбрать обложку
                </label>
                {coverImagePreview && (
                  <button
                    type="button"
                    className={styles.cancelButton}
                    onClick={() => {
                      URL.revokeObjectURL(coverImagePreview);
                      setCoverImagePreview(null);
                      setCoverImage(null);
                      coverImageInputRef.current.value = "";
                    }}
                  >
                    Отменить
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="genres">Жанры:</label>
          <select
            id="genres"
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

        <button
          type="submit"
          className={styles.submitButton}
          disabled={loading || !audioFile}
        >
          {loading ? "Загрузка..." : "Загрузить трек"}
        </button>
      </form>
    </div>
  );
});

export default UploadTrack;
