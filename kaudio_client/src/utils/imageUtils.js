/**
 * Преобразует относительный URL изображения в полный URL
 * @param {string} relativeUrl - Относительный URL изображения (например /media/profile_images/file.jpg)
 * @returns {string} Полный URL к изображению
 */
import { toJS } from "mobx";

export const getFullImageUrl = (url) => {
  console.log("getFullImageUrl вызван с URL:", url);

  if (!url) {
    console.log("getFullImageUrl: URL не предоставлен");
    return null;
  }

  // Проверяем, является ли URL уже полным (начинается с http или https)
  if (url.startsWith("http://") || url.startsWith("https://")) {
    console.log(
      "getFullImageUrl: URL уже полный, возвращаем без изменений:",
      url
    );
    return url;
  }

  // Если URL начинается с /, убираем его для корректного соединения с базовым URL
  const cleanUrl = url.startsWith("/") ? url.substring(1) : url;
  const fullUrl = `http://localhost:8000/${cleanUrl}`;

  console.log("getFullImageUrl: Сформирован полный URL:", fullUrl);
  return fullUrl;
};

/**
 * Возвращает первую букву имени пользователя для аватара-заполнителя
 * @param {string} username - Имя пользователя
 * @returns {string} Первая буква имени или дефолтное значение
 */
export const getAvatarInitial = (username) => {
  if (!username) return "U";
  return username[0].toUpperCase();
};

export const getImageUrl = (imageObject) => {
  if (typeof imageObject === "string") {
    return imageObject;
  }

  // Новые поля
  return (
    imageObject?.profile_image_url || // для пользователей
    imageObject?.cover_image_url || // для артистов
    imageObject?.cover_image_url || // для альбомов/треков
    // Оставляем старые поля для обратной совместимости
    imageObject?.img_profile_url ||
    imageObject?.img_cover_url ||
    imageObject?.img_url ||
    null
  );
};

// Функция для загрузки изображений
export const uploadImage = async (file, endpoint) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await instance.post(endpoint, formData);
  return {
    url: response.data.url || response.data.image_url,
    imageData: response.data,
  };
};
