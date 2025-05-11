import axios from "axios";

const instance = axios.create({
  baseURL: "http://localhost:8000/api/",
});

// Получаем токен из localStorage (проверяем оба возможных ключа)
const getAuthToken = () => {
  return localStorage.getItem("token") || localStorage.getItem("authToken");
};

// Добавляем интерцептор для логирования запросов и добавления токена
instance.interceptors.request.use(
  (config) => {
    // Получаем токен
    const token = getAuthToken();

    // Если токен есть, добавляем его в заголовки
    if (token) {
      config.headers.Authorization = `Token ${token}`;
      console.log("Добавлен токен авторизации в запрос:", `Token ${token}`);
    } else {
      console.warn(
        "Токен авторизации отсутствует при выполнении запроса к:",
        config.url
      );
    }

    console.log(
      `[Запрос отправлен] ${config.method.toUpperCase()} ${config.baseURL}${
        config.url
      }`,
      {
        headers: config.headers,
        data: config.data,
        params: config.params,
      }
    );
    return config;
  },
  (error) => {
    console.error("[Ошибка запроса]", error);
    return Promise.reject(error);
  }
);

// Добавляем интерцептор для логирования ответов
instance.interceptors.response.use(
  (response) => {
    console.log(
      `[Ответ получен] ${
        response.status
      } ${response.config.method.toUpperCase()} ${response.config.baseURL}${
        response.config.url
      }`,
      {
        data: response.data,
      }
    );
    return response;
  },
  (error) => {
    console.error(
      `[Ошибка ответа] ${error.response?.status || "Unknown"} ${
        error.config?.method.toUpperCase() || "Unknown"
      } ${error.config?.baseURL || ""}${error.config?.url || ""}`,
      {
        error: error.response?.data,
      }
    );
    return Promise.reject(error);
  }
);

export default instance;
