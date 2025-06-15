import React, { useState, useRef, useEffect } from "react";
import { observer } from "mobx-react-lite";
import { useNavigate, Link } from "react-router-dom";
import authStore from "../../stores/authStore";
import instance from "../../axios/axios";
import { getFullImageUrl } from "../../utils/imageUtils";
import styles from "./UploadAlbum.module.scss";

const UploadAlbum = observer(() => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });

  const [coverImage, setCoverImage] = useState(null);
  const [coverImagePreview, setCoverImagePreview] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [step, setStep] = useState(1); // 1 - основная информация, 2 - добавление треков
  const [isUserArtist, setIsUserArtist] = useState(true); // Статус пользователя как артиста

  const [newTrack, setNewTrack] = useState({
    title: "",
    audioFile: null,
    duration: 0,
  });

  const coverImageInputRef = useRef(null);
  const audioFileInputRef = useRef(null);

  const navigate = useNavigate();

  useEffect(() => {
    // Проверяем авторизацию
    if (!authStore.isAuthenticated) {
      navigate("/auth");
      return;
    }

    // Проверяем статус артиста, но не делаем перенаправление
    if (!authStore.isArtist) {
      setIsUserArtist(false);
      setError(
        "Для загрузки альбома вам необходимо иметь статус артиста. Перейдите в настройки профиля, чтобы получить этот статус."
      );
    } else {
      setIsUserArtist(true);
    }
  }, [navigate]);

  // Обработчик изменения текстовых полей альбома
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Обработчик изменения текстовых полей трека
  const handleTrackChange = (e) => {
    const { name, value } = e.target;
    setNewTrack((prev) => ({
      ...prev,
      [name]: value,
    }));
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

  // Обработчик выбора аудиофайла для трека
  const handleAudioFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith("audio/")) {
      setError("Пожалуйста, выберите аудиофайл");
      return;
    }

    setNewTrack((prev) => ({
      ...prev,
      audioFile: file,
    }));

    // Извлекаем длительность аудиофайла
    const audio = document.createElement("audio");
    audio.src = URL.createObjectURL(file);

    audio.onloadedmetadata = () => {
      const durationInSeconds = Math.round(audio.duration);
      setNewTrack((prev) => ({
        ...prev,
        duration: durationInSeconds,
      }));
    };

    audio.onerror = () => {
      setError("Не удалось прочитать аудиофайл");
    };
  };

  // Добавление трека в список
  const addTrack = (e) => {
    e.preventDefault();

    if (!newTrack.title || !newTrack.audioFile) {
      setError("Заполните все поля трека");
      return;
    }

    setTracks((prevTracks) => [
      ...prevTracks,
      { ...newTrack, id: Date.now() }, // Временный id для отслеживания
    ]);

    // Сбрасываем форму нового трека
    setNewTrack({
      title: "",
      audioFile: null,
      duration: 0,
    });

    // Сбрасываем input файла
    if (audioFileInputRef.current) {
      audioFileInputRef.current.value = "";
    }

    setError(null);
  };

  // Удаление трека из списка
  const removeTrack = (trackId) => {
    setTracks((prevTracks) =>
      prevTracks.filter((track) => track.id !== trackId)
    );
  };

  // Переход к следующему шагу
  const goToNextStep = (e) => {
    e.preventDefault();

    if (!formData.title || !coverImage) {
      setError("Заполните все обязательные поля");
      return;
    }

    setStep(2);
    setError(null);
  };

  // Возврат к предыдущему шагу
  const goToPreviousStep = () => {
    setStep(1);
  };

  // Отправка формы
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (tracks.length === 0) {
      setError("Добавьте хотя бы один трек в альбом");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Сначала создаем альбом с временными данными, чтобы получить ID
      const albumData = {
        title: formData.title,
        description: formData.description || "",
        artist_id: authStore.artistProfile.id,
        release_date: new Date().toISOString().split("T")[0], // Формат YYYY-MM-DD
        total_tracks: tracks.length,
        total_duration: tracks.reduce((sum, track) => sum + track.duration, 0),
        img_url: null, // Изначально null, URL добавим после загрузки обложки
      };

      console.log("Создание альбома:", albumData);
      const albumResponse = await instance.post("albums/", albumData);
      const albumId = albumResponse.data.id;

      // Затем загружаем обложку, если она выбрана
      let coverUrl = null;
      if (coverImage) {
        try {
          const coverFormData = new FormData();
          coverFormData.append("image", coverImage);
          coverFormData.append("album_id", albumId);

          const coverResponse = await instance.post(
            "upload/album-image/",
            coverFormData
          );
          coverUrl = coverResponse.data.img_url;
        } catch (coverError) {
          console.error("Ошибка при загрузке обложки альбома:", coverError);
          console.log("Детали ошибки:", coverError.response?.data);
          coverUrl = authStore.artistProfile.img_cover_url || "";
        }
      } else {
        coverUrl = authStore.artistProfile.img_cover_url || "";
      }

      // Загружаем треки и привязываем их к альбому
      console.log("Загрузка треков...");
      for (let i = 0; i < tracks.length; i++) {
        const track = tracks[i];
        const trackFormData = new FormData();
        trackFormData.append("audio_file", track.audioFile);
        trackFormData.append("title", track.title);
        trackFormData.append("artist_id", authStore.artistProfile.id);
        trackFormData.append("duration", track.duration);
        trackFormData.append("album_id", albumId);
        trackFormData.append("track_number", i + 1); // Номер трека в порядке следования

        // Если есть обложка, добавляем URL
        if (coverUrl) {
          trackFormData.append("img_url", coverUrl);
        } else {
          trackFormData.append("img_url", ""); // Пустая строка, если обложки нет
        }

        await instance.post("upload/track/", trackFormData);
      }

      setSuccess("Альбом успешно создан!");

      // Очищаем форму
      setFormData({
        title: "",
        description: "",
      });
      setCoverImage(null);
      if (coverImagePreview) URL.revokeObjectURL(coverImagePreview);
      setCoverImagePreview(null);
      setTracks([]);
      setStep(1);

      // Перенаправляем на страницу альбома
      setTimeout(() => {
        navigate(`/albums/${albumId}`);
      }, 1500);
    } catch (error) {
      console.error("Ошибка при создании альбома:", error);
      console.log("Детали ошибки:", error.response?.data);
      console.log("Статус ошибки:", error.response?.status);
      // Обработка ошибки уникальности трека в альбоме
      if (
        (error.response?.status === 500 &&
          String(error.response?.data).includes("UNIQUE constraint failed")) ||
        (typeof error.response?.data?.error === "string" &&
          error.response.data.error.includes("UNIQUE constraint failed"))
      ) {
        setError(
          "В альбоме не может быть двух треков с одинаковым названием. Пожалуйста, выберите уникальные названия для каждого трека."
        );
      } else if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError("Не удалось создать альбом");
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
      <h1 className={styles.title}>Создание альбома</h1>

      {error && <div className={styles.error}>{error}</div>}
      {success && <div className={styles.success}>{success}</div>}

      {!isUserArtist && (
        <div className={styles.artistRequiredMessage}>
          <p>Для загрузки альбома необходимо иметь статус артиста.</p>
          <Link to="/settings" className={`${styles.button} ${styles.primary}`}>
            Перейти в настройки профиля
          </Link>
        </div>
      )}

      {isUserArtist && step === 1 && (
        <form onSubmit={goToNextStep} className={styles.uploadForm}>
          <h2>Шаг 1: Информация об альбоме</h2>

          <div className={styles.formGroup}>
            <label htmlFor="title">Название альбома:</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              className={styles.input}
              placeholder="Введите название альбома"
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Описание (необязательно):</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              className={styles.textarea}
              placeholder="Добавьте описание альбома"
              rows={4}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="coverImage">Обложка альбома:</label>
            <div className={styles.fileInputWrapper}>
              <input
                type="file"
                id="coverImage"
                accept="image/*"
                ref={coverImageInputRef}
                onChange={handleCoverImageChange}
                required
                className={styles.fileInput}
              />
              <label htmlFor="coverImage" className={styles.fileInputLabel}>
                {coverImage ? coverImage.name : "Выберите изображение обложки"}
              </label>
            </div>

            {coverImagePreview && (
              <div className={styles.imagePreview}>
                <img
                  src={coverImagePreview}
                  alt="Предпросмотр обложки"
                  className={styles.previewImage}
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            className={`${styles.button} ${styles.primary}`}
            disabled={loading}
          >
            Далее
          </button>
        </form>
      )}

      {isUserArtist && step === 2 && (
        <div className={styles.stepContainer}>
          <h2>Шаг 2: Добавление треков</h2>

          <div className={styles.tracksList}>
            <h3>Треки в альбоме ({tracks.length})</h3>

            {tracks.length === 0 ? (
              <p>В альбоме пока нет треков. Добавьте треки ниже.</p>
            ) : (
              <ul className={styles.tracks}>
                {tracks.map((track, index) => (
                  <li key={track.id} className={styles.trackItem}>
                    <span className={styles.trackNumber}>{index + 1}.</span>
                    <span className={styles.trackTitle}>{track.title}</span>
                    <span className={styles.trackDuration}>
                      {Math.floor(track.duration / 60)}:
                      {String(track.duration % 60).padStart(2, "0")}
                    </span>
                    <button
                      type="button"
                      className={`${styles.button} ${styles.remove}`}
                      onClick={() => removeTrack(track.id)}
                    >
                      Удалить
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <form onSubmit={addTrack} className={styles.trackForm}>
            <h3>Добавить новый трек</h3>

            <div className={styles.formGroup}>
              <label htmlFor="trackTitle">Название трека:</label>
              <input
                type="text"
                id="trackTitle"
                name="title"
                value={newTrack.title}
                onChange={handleTrackChange}
                required
                className={styles.input}
                placeholder="Введите название трека"
              />
            </div>

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
                  {newTrack.audioFile
                    ? newTrack.audioFile.name
                    : "Выберите аудиофайл"}
                </label>
              </div>

              {newTrack.duration > 0 && (
                <div className={styles.durationInfo}>
                  Длительность: {Math.floor(newTrack.duration / 60)}:
                  {String(newTrack.duration % 60).padStart(2, "0")}
                </div>
              )}
            </div>

            <button
              type="submit"
              className={`${styles.button} ${styles.secondary}`}
            >
              Добавить трек
            </button>
          </form>

          <div className={styles.formActions}>
            <button
              type="button"
              className={`${styles.button} ${styles.secondary}`}
              onClick={goToPreviousStep}
            >
              Назад
            </button>

            <button
              type="button"
              className={`${styles.button} ${styles.primary}`}
              onClick={handleSubmit}
              disabled={loading || tracks.length === 0}
            >
              {loading ? "Создание альбома..." : "Создать альбом"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

export default UploadAlbum;
