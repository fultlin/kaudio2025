/**
 * Форматирует длительность из секунд в формат MM:SS
 * @param {number} seconds - Длительность в секундах
 * @returns {string} Отформатированная длительность
 */
const formatDuration = (seconds) => {
  if (!seconds) return "0:00";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
};

/**
 * Форматирует дату в локальный формат
 * @param {string} dateString - Дата в формате ISO
 * @returns {string} Отформатированная дата
 */
const formatDate = (dateString) => {
  if (!dateString) return "";

  return new Date(dateString).toLocaleDateString("ru-RU", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

/**
 * Форматирует число с разделителями тысяч
 * @param {number} number - Число для форматирования
 * @returns {string} Отформатированное число
 */
export const formatNumber = (number) => {
  if (!number && number !== 0) return "";

  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
};

/**
 * Форматирует размер файла в читаемый формат
 * @param {number} bytes - Размер в байтах
 * @returns {string} Отформатированный размер
 */
export const formatFileSize = (bytes) => {
  if (!bytes) return "0 Б";

  const sizes = ["Б", "КБ", "МБ", "ГБ"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));

  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
};

/**
 * Форматирует строку, обрезая её до указанной длины
 * @param {string} str - Исходная строка
 * @param {number} maxLength - Максимальная длина
 * @returns {string} Отформатированная строка
 */
export const truncateString = (str, maxLength = 50) => {
  if (!str) return "";
  if (str.length <= maxLength) return str;

  return str.slice(0, maxLength - 3) + "...";
};

// Экспортируем все функции
export { formatDuration, formatDate };

// Добавляем default export
export default {
  formatDuration,
  formatDate,
};
