/**
 * Преобразует относительный URL изображения в полный URL
 * @param {string} relativeUrl - Относительный URL изображения (например /media/profile_images/file.jpg)
 * @returns {string} Полный URL к изображению
 */
export const getFullImageUrl = (relativeUrl) => {
  if (!relativeUrl) return null;

  // Если URL уже абсолютный, возвращаем как есть
  if (relativeUrl.startsWith("http://") || relativeUrl.startsWith("https://")) {
    return relativeUrl;
  }

  // Иначе добавляем базовый URL сервера
  return `http://localhost:8000${relativeUrl}`;
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
