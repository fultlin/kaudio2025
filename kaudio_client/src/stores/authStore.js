import { makeAutoObservable, action, observable } from "mobx";
import instance from "../axios/axios";
import { getFullImageUrl } from "../utils/imageUtils";

class AuthStore {
  user = null;
  artistProfile = null;
  isAuthenticated = false;
  isArtist = false;
  isAdmin = false;
  loading = false;
  error = null;
  lastArtistCheck = null;
  artistCheckTimeout = 5000; // 5 секунд между проверками

  constructor() {
    makeAutoObservable(this, {
      user: observable,
      isAuthenticated: observable,
      artistProfile: observable,
      isAdmin: observable,
      loading: observable,
      error: observable,
      login: action,
      logout: action,
      register: action,
      checkAuth: action,
      setUser: action,
      setIsAuthenticated: action,
      setIsLoading: action,
      setError: action,
      setArtistProfile: action,
    });
    this.checkAuth();
  }

  setUser = (user) => {
    console.log("AuthStore.setUser: Получены данные пользователя:", user);
    this.user = user;
    this.isAuthenticated = !!user;
    this.isAdmin = user?.role === "admin";
    this.isArtist = user?.role === "artist";
    console.log("AuthStore.setUser: isAdmin установлен в:", this.isAdmin);
    console.log("AuthStore.setUser: isArtist установлен в:", this.isArtist);
  };

  setIsAuthenticated(status) {
    this.isAuthenticated = status;
  }

  setIsLoading(status) {
    this.loading = status;
  }

  setError(error) {
    this.error = error;
  }

  setArtistProfile = (profile) => {
    this.artistProfile = profile;
    this.isArtist = !!profile;
  };

  checkAuth = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      this.setUser(null);
      this.setArtistProfile(null);
      this.isAuthenticated = false;
      this.isArtist = false;
      return;
    }

    try {
      const response = await instance.get("users/me/");
      this.setUser(response.data);
      this.isAuthenticated = true;

      // Проверяем статус артиста сразу после получения данных пользователя
      await this.checkArtistStatus();
    } catch (error) {
      console.error("Ошибка при проверке авторизации:", error);
      this.setUser(null);
      this.setArtistProfile(null);
      this.isAuthenticated = false;
      this.isArtist = false;
      localStorage.removeItem("token");
    }
  };

  checkArtistStatus = async () => {
    if (!this.user) return;

    try {
      const response = await instance.get(`artists/?user=${this.user.id}`);
      console.log("AuthStore.checkArtistStatus: Ответ сервера:", response.data);

      if (response.data && response.data.length > 0) {
        const artist = response.data[0];
        // Проверяем, что артист действительно связан с текущим пользователем
        if (artist.user && artist.user.id === this.user.id) {
          console.log("AuthStore.checkArtistStatus: Найден артист", artist);

          // Сохраняем профиль артиста
          this.setArtistProfile(artist);

          // Добавляем информацию об артисте в объект пользователя
          this.setUser({
            ...this.user,
            artist: artist,
            img_profile_url: this.user.img_profile_url
              ? getFullImageUrl(this.user.img_profile_url)
              : null,
          });

          // Устанавливаем флаг isArtist
          this.isArtist = true;
        } else {
          console.log(
            "AuthStore.checkArtistStatus: Артист не связан с текущим пользователем"
          );
          this.setArtistProfile(null);
          this.setUser({
            ...this.user,
            artist: null,
            img_profile_url: this.user.img_profile_url
              ? getFullImageUrl(this.user.img_profile_url)
              : null,
          });
          this.isArtist = false;
        }
      } else {
        console.log("AuthStore.checkArtistStatus: Артист не найден");
        this.setArtistProfile(null);
        this.setUser({
          ...this.user,
          artist: null,
          img_profile_url: this.user.img_profile_url
            ? getFullImageUrl(this.user.img_profile_url)
            : null,
        });
        this.isArtist = false;
      }
    } catch (error) {
      console.error("Ошибка при проверке статуса артиста:", error);
      this.setArtistProfile(null);
      this.isArtist = false;
    }
  };

  // Метод для принудительного обновления данных артиста
  forceCheckArtistStatus = async () => {
    this.lastArtistCheck = null;
    await this.checkArtistStatus();
  };

  async login(username, password) {
    console.log("AuthStore.login: Выполняем вход для пользователя", username);
    this.setIsLoading(true);
    this.setError(null);

    console.log("Отправка данных для входа:", { username, password }); // Для отладки

    try {
      const response = await instance.post("auth/login/", {
        username,
        password,
      });

      console.log("AuthStore.login: Получен ответ:", response.data);

      const { token, user } = response.data;

      if (!token) {
        throw new Error("Токен не получен");
      }

      localStorage.setItem("token", token);
      instance.defaults.headers.common["Authorization"] = `Token ${token}`;

      this.setUser(user);
      this.setIsAuthenticated(true);

      await this.checkArtistStatus();

      console.log("AuthStore.login: Пользователь авторизован", this.user);

      return true;
    } catch (error) {
      console.error("AuthStore.login: Ошибка при входе:", error);
      console.error(
        "AuthStore.login: Детали ошибки:",
        error.response?.data || error.message
      );

      let errorMessage = "Неверное имя пользователя или пароль";

      if (error.response && error.response.data) {
        errorMessage = error.response.data.error || errorMessage;
      }

      this.setError(errorMessage);
      return false;
    } finally {
      this.setIsLoading(false);
    }
  }

  async logout() {
    console.log("AuthStore.logout: Выполняем выход пользователя");
    // Удаляем токен из localStorage
    localStorage.removeItem("token");
    delete instance.defaults.headers.common["Authorization"];

    // Сбрасываем состояние
    this.setUser(null);
    this.setIsAuthenticated(false);

    console.log("AuthStore.logout: Пользователь вышел из системы");
  }

  async register(userData) {
    console.log(
      "AuthStore.register: Регистрируем нового пользователя",
      userData.username || userData.login
    );
    this.setIsLoading(true);
    this.setError(null);

    try {
      await instance.post("auth/register/", {
        username: userData.username || userData.login,
        email: userData.email,
        password: userData.password,
      });

      return await this.login(
        userData.username || userData.login,
        userData.password
      );
    } catch (error) {
      console.error("AuthStore.register: Ошибка при регистрации:", error);
      console.error(
        "AuthStore.register: Детали ошибки:",
        error.response?.data || error.message
      );

      let errorMessage = "Ошибка регистрации";

      if (error.response && error.response.data) {
        errorMessage = error.response.data.error || errorMessage;
      }

      this.setError(errorMessage);
      return false;
    } finally {
      this.setIsLoading(false);
    }
  }
}

export default new AuthStore();
