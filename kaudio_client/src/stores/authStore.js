import { makeAutoObservable } from "mobx";
import instance from "../axios/axios";

class AuthStore {
  user = null;
  isAuthenticated = false;
  artistProfile = null;
  loading = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
    this.checkAuth();
  }

  checkAuth = async () => {
    const token = localStorage.getItem("token");
    if (token) {
      instance.defaults.headers.common["Authorization"] = `Token ${token}`;
      try {
        const response = await instance.get("users/me/");
        this.user = response.data;
        this.isAuthenticated = true;

        await this.checkArtistStatus();
      } catch (error) {
        this.logout();
        this.error = "Ошибка аутентификации";
      }
    }
  };

  checkArtistStatus = async () => {
    if (!this.user) return;

    try {
      const artistsRes = await instance.get(
        `artists/?email=${this.user.email}`
      );
      if (artistsRes.data && artistsRes.data.length > 0) {
        this.artistProfile = artistsRes.data[0];
      } else {
        this.artistProfile = null;
      }
    } catch (error) {
      console.error("Ошибка при проверке статуса исполнителя:", error);
      this.artistProfile = null;
    }
  };

  get isArtist() {
    return !!this.artistProfile;
  }

  login = async (username, password) => {
    this.loading = true;
    this.error = null;

    console.log("Отправка данных для входа:", { username, password }); // Для отладки

    try {
      const response = await instance.post("auth/login/", {
        username,
        password,
      });

      console.log("Ответ сервера:", response.data); // Для отладки

      const { token, user } = response.data;

      if (!token) {
        throw new Error("Токен не получен");
      }

      localStorage.setItem("token", token);
      instance.defaults.headers.common["Authorization"] = `Token ${token}`;

      this.user = user;
      this.isAuthenticated = true;

      return true;
    } catch (error) {
      console.error("Ошибка авторизации:", error);
      console.error("Детали ошибки:", error.response?.data); // Для отладки

      this.error =
        error.response?.data?.error ||
        error.response?.data?.non_field_errors?.[0] ||
        error.response?.data?.detail ||
        "Неверное имя пользователя или пароль";
      return false;
    } finally {
      this.loading = false;
    }
  };

  register = async (userData) => {
    this.loading = true;
    this.error = null;

    try {
      await instance.post("auth/register/", {
        username: userData.username || userData.login,
        email: userData.email,
        password: userData.password,
      });

      return true;
    } catch (error) {
      console.error("Ошибка регистрации:", error);

      const errorData = error.response?.data;
      if (typeof errorData === "object") {
        const errorMessages = [];
        for (const field in errorData) {
          errorMessages.push(`${field}: ${errorData[field].join(", ")}`);
        }
        this.error = errorMessages.join("\n");
      } else {
        this.error = error.response?.data?.error || "Ошибка регистрации";
      }

      return false;
    } finally {
      this.loading = false;
    }
  };

  logout = () => {
    localStorage.removeItem("token");
    delete instance.defaults.headers.common["Authorization"];
    this.user = null;
    this.isAuthenticated = false;
  };
}

export default new AuthStore();
