import React, { useState, useEffect, useRef } from "react";
import { observer } from "mobx-react-lite";
import instance from "../../axios/axios";
import authStore from "../../stores/authStore";
import { useNavigate } from "react-router-dom";
import styles from "./Settings.module.scss";
import { getFullImageUrl, getAvatarInitial } from "../../utils/imageUtils";
import debounce from "lodash/debounce";

const Settings = observer(() => {
  const [userProfile, setUserProfile] = useState({
    username: "",
    email: "",
    img_profile_url: "",
  });

  const [originalUserProfile, setOriginalUserProfile] = useState({
    username: "",
    email: "",
    img_profile_url: "",
  });

  const [artistProfile, setArtistProfile] = useState({
    id: null,
    username: "",
    bio: "",
    img_cover_url: "",
    monthly_listeners: 0,
    is_verified: false,
  });

  const [originalArtistProfile, setOriginalArtistProfile] = useState({
    id: null,
    username: "",
    bio: "",
    img_cover_url: "",
    monthly_listeners: 0,
    is_verified: false,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showArtistForm, setShowArtistForm] = useState(false);

  // Refs для input file
  const profileImageInputRef = useRef(null);
  const artistImageInputRef = useRef(null);

  // Состояния для предпросмотра файлов
  const [profileImagePreview, setProfileImagePreview] = useState(null);
  const [artistImagePreview, setArtistImagePreview] = useState(null);

  const navigate = useNavigate();

  // Создаем дебаунсированную версию функции получения данных артиста
  const debouncedFetchArtistData = debounce(async (userId) => {
    try {
      const artistsRes = await instance.get(`artists/?user=${userId}`);
      if (artistsRes.data && artistsRes.data.length > 0) {
        const artist = artistsRes.data[0];
        if (
          (artist.user && artist.user.id === userId) ||
          (!artist.user && artist.id)
        ) {
          const artistData = {
            id: artist.id,
            username: artist.username,
            bio: artist.bio || "",
            img_cover_url: artist.img_cover_url || "",
            monthly_listeners: artist.monthly_listeners || 0,
            is_verified: artist.is_verified || false,
            user: artist.user,
          };
          setArtistProfile(artistData);
          setOriginalArtistProfile(artistData);
          if (authStore.setArtistProfile) {
            authStore.setArtistProfile(artist);
          }
        }
      }
    } catch (error) {
      console.error("Ошибка при получении данных артиста:", error);
    }
  }, 300);

  // Загрузка данных пользователя и его профиля исполнителя
  useEffect(() => {
    if (!authStore.isAuthenticated) {
      navigate("/auth");
      return;
    }

    const fetchUserData = async () => {
      setLoading(true);
      try {
        const userRes = await instance.get("users/me/");
        const userData = {
          username: userRes.data.username,
          email: userRes.data.email,
          img_profile_url: userRes.data.img_profile_url || "",
        };

        setUserProfile(userData);
        setOriginalUserProfile(userData);

        // Используем дебаунсированную версию для получения данных артиста
        debouncedFetchArtistData(userRes.data.id);
      } catch (error) {
        setError("Ошибка при загрузке данных пользователя");
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();

    // Очистка при размонтировании компонента
    return () => {
      debouncedFetchArtistData.cancel();
    };
  }, []);

  // Обработчик изменения полей профиля пользователя
  const handleUserProfileChange = (e) => {
    const { name, value } = e.target;
    setUserProfile((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Обработчик изменения полей профиля исполнителя
  const handleArtistProfileChange = (e) => {
    const { name, value } = e.target;
    setArtistProfile((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Обработчик выбора файла изображения профиля
  const handleProfileImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Проверка типа файла
    if (!file.type.match("image.*")) {
      setError("Пожалуйста, выберите изображение");
      return;
    }

    // Создаем URL для предпросмотра
    const previewUrl = URL.createObjectURL(file);
    setProfileImagePreview(previewUrl);
  };

  // Обработчик выбора файла изображения исполнителя
  const handleArtistImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Проверка типа файла
    if (!file.type.match("image.*")) {
      setError("Пожалуйста, выберите изображение");
      return;
    }

    // Создаем URL для предпросмотра
    const previewUrl = URL.createObjectURL(file);
    setArtistImagePreview(previewUrl);
  };

  // Функция загрузки изображения профиля
  const uploadProfileImage = async () => {
    if (!profileImageInputRef.current?.files?.length) return null;

    const file = profileImageInputRef.current.files[0];
    const formData = new FormData();
    formData.append("image", file);

    try {
      console.log("Файл для загрузки:", file);

      // Используем стандартный путь API
      const response = await instance.post("upload/profile-image/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Ответ сервера:", response.data);

      setSuccess("Изображение профиля успешно загружено");

      // Очищаем предпросмотр и инпут
      URL.revokeObjectURL(profileImagePreview);
      setProfileImagePreview(null);
      profileImageInputRef.current.value = "";

      return response.data.img_profile_url;
    } catch (err) {
      console.error("Ошибка при загрузке изображения профиля:", err);
      setError(
        err.response?.data?.error || "Не удалось загрузить изображение профиля"
      );
      return null;
    }
  };

  // Функция загрузки изображения исполнителя
  const uploadArtistImage = async () => {
    if (!artistImageInputRef.current?.files?.length) return null;

    // Проверяем, что ID артиста установлен
    if (!artistProfile.id) {
      console.error("ID артиста не определен, загрузка изображения невозможна");
      setError("Невозможно загрузить изображение: профиль артиста не создан");
      return null;
    }

    const file = artistImageInputRef.current.files[0];
    const formData = new FormData();
    formData.append("image", file);
    formData.append("artist_id", artistProfile.id);

    try {
      console.log("Файл для загрузки обложки исполнителя:", file);
      console.log("ID артиста для загрузки:", artistProfile.id);

      // Используем стандартный путь API
      const response = await instance.post("upload/artist-image/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Ответ сервера:", response.data);

      setSuccess("Изображение исполнителя успешно загружено");

      // Очищаем предпросмотр и инпут
      URL.revokeObjectURL(artistImagePreview);
      setArtistImagePreview(null);
      artistImageInputRef.current.value = "";

      return response.data.img_cover_url;
    } catch (err) {
      console.error("Ошибка при загрузке изображения исполнителя:", err);
      setError(
        err.response?.data?.error ||
          "Не удалось загрузить изображение исполнителя"
      );
      return null;
    }
  };

  // Проверяем, были ли изменены данные пользователя
  const isUserProfileModified = () => {
    if (!authStore.user) return false;

    return (
      userProfile.username !== originalUserProfile.username ||
      userProfile.email !== originalUserProfile.email ||
      profileImagePreview !== null
    );
  };

  // Проверяем, были ли изменены данные артиста
  const isArtistProfileModified = () => {
    if (!authStore.isArtist) return true; // Если профиля нет, то всегда разрешаем создание

    // Проверяем изменения в существующем профиле
    return (
      artistProfile.bio !== originalArtistProfile.bio ||
      artistImagePreview !== null
    );
  };

  // Проверка, изменилось ли конкретное поле пользовательского профиля
  const isUserFieldModified = (fieldName) => {
    return userProfile[fieldName] !== originalUserProfile[fieldName];
  };

  // Проверка, изменилось ли конкретное поле профиля артиста
  const isArtistFieldModified = (fieldName) => {
    return artistProfile[fieldName] !== originalArtistProfile[fieldName];
  };

  // Обработчик сохранения профиля пользователя
  const handleSaveUserProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Если есть новое изображение, загружаем его
      let imageUrl = userProfile.img_profile_url;
      if (profileImagePreview) {
        const uploadedImage = await uploadProfileImage();
        if (uploadedImage) {
          imageUrl = uploadedImage;
        }
      }

      // Преобразуем относительный URL в полный URL, если это необходимо
      const fullImageUrl = imageUrl ? getFullImageUrl(imageUrl) : null;

      // Обновленные данные профиля
      const updatedUserProfile = {
        ...userProfile,
        img_profile_url: imageUrl, // Сохраняем оригинальный URL в состоянии
      };

      // Обновляем данные профиля
      await instance.patch(`users/${authStore.user.id}/`, {
        username: updatedUserProfile.username,
        email: updatedUserProfile.email,
        img_profile_url: fullImageUrl, // Отправляем полный URL на сервер
      });

      // Обновляем информацию о пользователе в authStore
      authStore.user = {
        ...authStore.user,
        username: updatedUserProfile.username,
        email: updatedUserProfile.email,
        img_profile_url: updatedUserProfile.img_profile_url,
      };

      // Обновляем локальные данные и оригинальные данные
      setUserProfile(updatedUserProfile);
      setOriginalUserProfile(updatedUserProfile);

      setSuccess("Профиль пользователя успешно обновлен");

      setTimeout(() => {
        navigate("/");
      }, 1500);
    } catch (err) {
      console.error("Ошибка при обновлении профиля пользователя:", err);
      setError(
        err.response?.data?.error || "Не удалось обновить профиль пользователя"
      );
    } finally {
      setLoading(false);
    }
  };

  // Обработчик сохранения/создания профиля исполнителя
  const handleSaveArtistProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      let response;
      // Если есть новое изображение, загружаем его
      let imageUrl = artistProfile.img_cover_url;

      if (authStore.isArtist && artistImagePreview) {
        const uploadedImage = await uploadArtistImage();
        if (uploadedImage) {
          imageUrl = uploadedImage;
        }
      }

      // Преобразуем относительный URL в полный URL, если это необходимо
      const fullImageUrl = imageUrl ? getFullImageUrl(imageUrl) : null;

      // Обновленные данные профиля
      const updatedArtistProfile = {
        ...artistProfile,
        img_cover_url: imageUrl, // Сохраняем оригинальный URL в состоянии
      };

      if (authStore.isArtist) {
        // Обновляем существующий профиль
        response = await instance.patch(`artists/${artistProfile.id}/`, {
          bio: updatedArtistProfile.bio,
          img_cover_url: fullImageUrl, // Отправляем полный URL на сервер
        });
      } else {
        // Создаем новый профиль
        response = await instance.post("artists/", {
          bio: updatedArtistProfile.bio,
        });
      }

      // После создания или обновления артиста — получаем свежий объект с вложенным user
      const artistsRes = await instance.get(
        `artists/?user=${authStore.user.id}`
      );
      if (artistsRes.data && artistsRes.data.length > 0) {
        const artist = artistsRes.data[0];
        const artistData = {
          id: artist.id,
          username: artist.username,
          bio: artist.bio || "",
          img_cover_url: artist.img_cover_url || "",
          monthly_listeners: artist.monthly_listeners || 0,
          is_verified: artist.is_verified || false,
          user: artist.user,
        };
        setArtistProfile(artistData);
        setOriginalArtistProfile(artistData);
        // Обновляем глобальный стор
        if (authStore.setArtistProfile) authStore.setArtistProfile(artist);
      }

      setSuccess(
        authStore.isArtist
          ? "Профиль исполнителя успешно обновлен"
          : "Профиль исполнителя успешно создан"
      );
    } catch (err) {
      console.error("Ошибка при сохранении профиля исполнителя:", err);
      setError(
        err.response?.data?.error || "Не удалось сохранить профиль исполнителя"
      );
    } finally {
      setLoading(false);
    }
  };

  // При размонтировании компонента очищаем URL-ы предпросмотра
  useEffect(() => {
    return () => {
      if (profileImagePreview) URL.revokeObjectURL(profileImagePreview);
      if (artistImagePreview) URL.revokeObjectURL(artistImagePreview);
    };
  }, [profileImagePreview, artistImagePreview]);

  // После успешного создания артиста сбрасываем showArtistForm
  useEffect(() => {
    if (authStore.isArtist) {
      setShowArtistForm(false);
    }
  }, [authStore.isArtist]);

  return (
    <div className={styles.settingsContainer}>
      <h1 className={styles.title}>Настройки профиля</h1>

      {error && <div className={styles.error}>{error}</div>}
      {success && <div className={styles.success}>{success}</div>}

      <div className={styles.settingsSections}>
        {/* Секция профиля пользователя */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Профиль пользователя</h2>
          <form onSubmit={handleSaveUserProfile}>
            <div className={styles.formGroup}>
              <label htmlFor="username">Имя пользователя</label>
              <input
                type="text"
                id="username"
                name="username"
                value={userProfile.username}
                onChange={handleUserProfileChange}
                className={`${styles.input} ${
                  isUserFieldModified("username") ? styles.modified : ""
                }`}
                required
                placeholder="Введите имя пользователя"
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={userProfile.email}
                onChange={handleUserProfileChange}
                className={`${styles.input} ${
                  isUserFieldModified("email") ? styles.modified : ""
                }`}
                required
                placeholder="Введите ваш email"
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="profileImage">Фото профиля</label>
              <div className={styles.imageUploadContainer}>
                <div className={styles.imagePreviewWrapper}>
                  {profileImagePreview ? (
                    <img
                      src={profileImagePreview}
                      alt="Предпросмотр"
                      className={styles.previewImg}
                    />
                  ) : userProfile.img_profile_url ? (
                    <img
                      src={getFullImageUrl(userProfile.img_profile_url)}
                      alt="Фото профиля"
                      className={styles.previewImg}
                    />
                  ) : (
                    <div className={styles.imagePlaceholder}>
                      <span>{getAvatarInitial(userProfile.username)}</span>
                    </div>
                  )}
                </div>
                <div className={styles.imageControls}>
                  <input
                    type="file"
                    id="profileImage"
                    ref={profileImageInputRef}
                    accept="image/*"
                    onChange={handleProfileImageChange}
                    className={styles.fileInput}
                  />
                  <label htmlFor="profileImage" className={styles.uploadButton}>
                    Выбрать фото
                  </label>
                  {profileImagePreview && (
                    <button
                      type="button"
                      className={styles.cancelButton}
                      onClick={() => {
                        URL.revokeObjectURL(profileImagePreview);
                        setProfileImagePreview(null);
                        profileImageInputRef.current.value = "";
                      }}
                    >
                      Отменить
                    </button>
                  )}
                </div>
              </div>
            </div>

            <button
              type="submit"
              className={styles.button}
              disabled={loading || !isUserProfileModified()}
            >
              {loading ? (
                <span className={styles.loadingIndicator}>
                  <span className={styles.loadingDot}></span>
                  <span className={styles.loadingDot}></span>
                  <span className={styles.loadingDot}></span>
                </span>
              ) : (
                "Сохранить профиль"
              )}
            </button>
            {!isUserProfileModified() ? (
              <p className={styles.infoText}>
                Внесите изменения для сохранения профиля
              </p>
            ) : (
              <p className={styles.modifiedText}>
                Профиль изменен. Нажмите кнопку для сохранения.
              </p>
            )}
          </form>
        </section>

        {/* Секция профиля исполнителя */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>
            {authStore.isArtist
              ? "Профиль исполнителя"
              : "Создать профиль исполнителя"}
          </h2>

          {/* Кнопка появляется только если нет артиста и не нажата форма */}
          {!authStore.isArtist && !showArtistForm && (
            <button
              className={styles.button}
              onClick={() => setShowArtistForm(true)}
              type="button"
            >
              Стать артистом
            </button>
          )}

          {/* Форма появляется только если есть артист или нажата кнопка */}
          {(authStore.isArtist || showArtistForm) && (
            <form onSubmit={handleSaveArtistProfile}>
              <div className={styles.formGroup}>
                <label htmlFor="bio">Биография</label>
                <textarea
                  id="bio"
                  name="bio"
                  value={artistProfile.bio}
                  onChange={handleArtistProfileChange}
                  className={`${styles.textarea} ${
                    isArtistFieldModified("bio") ? styles.modified : ""
                  }`}
                  rows="5"
                  placeholder="Расскажите о себе как об исполнителе..."
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="artistImage">Фото обложки исполнителя</label>
                <div className={styles.imageUploadContainer}>
                  <div className={styles.imagePreviewWrapper}>
                    {artistImagePreview ? (
                      <img
                        src={artistImagePreview}
                        alt="Предпросмотр обложки"
                        className={styles.previewImg}
                      />
                    ) : artistProfile.img_cover_url ? (
                      <img
                        src={getFullImageUrl(artistProfile.img_cover_url)}
                        alt="Фото исполнителя"
                        className={styles.previewImg}
                      />
                    ) : (
                      <div className={styles.imagePlaceholder}>
                        <span>{getAvatarInitial(userProfile.username)}</span>
                      </div>
                    )}
                  </div>
                  <div className={styles.imageControls}>
                    <input
                      type="file"
                      id="artistImage"
                      ref={artistImageInputRef}
                      accept="image/*"
                      onChange={handleArtistImageChange}
                      className={styles.fileInput}
                    />
                    <label
                      htmlFor="artistImage"
                      className={styles.uploadButton}
                    >
                      Выбрать фото
                    </label>
                    {artistImagePreview && (
                      <button
                        type="button"
                        className={styles.cancelButton}
                        onClick={() => {
                          URL.revokeObjectURL(artistImagePreview);
                          setArtistImagePreview(null);
                          artistImageInputRef.current.value = "";
                        }}
                      >
                        Отменить
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {authStore.isArtist && (
                <div className={styles.formGroup}>
                  <p className={styles.infoText}>
                    <strong>Количество прослушиваний:</strong>{" "}
                    {artistProfile.monthly_listeners}
                  </p>
                  <p className={styles.infoText}>
                    <strong>Статус верификации:</strong>{" "}
                    {artistProfile.is_verified
                      ? "Подтвержден"
                      : "Не подтвержден"}
                  </p>
                </div>
              )}

              <button
                type="submit"
                className={styles.button}
                disabled={loading || !isArtistProfileModified()}
              >
                {loading ? (
                  <span className={styles.loadingIndicator}>
                    <span className={styles.loadingDot}></span>
                    <span className={styles.loadingDot}></span>
                    <span className={styles.loadingDot}></span>
                  </span>
                ) : authStore.isArtist ? (
                  "Обновить профиль исполнителя"
                ) : (
                  "Создать профиль исполнителя"
                )}
              </button>
              {authStore.isArtist && !isArtistProfileModified() ? (
                <p className={styles.infoText}>
                  Внесите изменения для обновления профиля исполнителя
                </p>
              ) : authStore.isArtist && isArtistProfileModified() ? (
                <p className={styles.modifiedText}>
                  Профиль изменен. Нажмите кнопку для сохранения.
                </p>
              ) : (
                <p className={styles.infoText}>
                  Создайте профиль исполнителя, чтобы загружать альбомы и треки
                </p>
              )}
            </form>
          )}
        </section>
      </div>
    </div>
  );
});

export default Settings;
