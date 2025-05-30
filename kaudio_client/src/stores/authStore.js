import { makeAutoObservable, action, observable } from "mobx";
import instance from "../axios/axios";
import { getFullImageUrl } from "../utils/imageUtils";

class AuthStore {
  user = null;
  isAuthenticated = false;
  artistProfile = null;
  loading = false;
  error = null;

  constructor() {
    makeAutoObservable(this, {
      user: observable,
      isAuthenticated: observable,
      artistProfile: observable,
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

  setUser(user) {
    this.user = user;
  }

  setIsAuthenticated(status) {
    this.isAuthenticated = status;
  }

  setIsLoading(status) {
    this.loading = status;
  }

  setError(error) {
    this.error = error;
  }

  setArtistProfile(artistProfile) {
    this.artistProfile = artistProfile;
  }

  checkAuth = async () => {
    console.log("AuthStore.checkAuth: Проверяем аутентификацию");
    const token = localStorage.getItem("token");

    if (!token) {
      console.log("AuthStore.checkAuth: Токен не найден");
      this.setIsAuthenticated(false);
      this.setUser(null);
      return false;
    }

    console.log("AuthStore.checkAuth: Токен найден:", token);

    // Устанавливаем токен в заголовки по умолчанию
    instance.defaults.headers.common["Authorization"] = `Token ${token}`;

    this.setIsLoading(true);

    try {
      console.log("AuthStore.checkAuth: Запрашиваем данные пользователя");
      // Проверяем валидность токена, запрашивая данные текущего пользователя
      const response = await instance.get("users/me/");

      console.log("AuthStore.checkAuth: Получен ответ:", response.data);

      // Если запрос успешен, устанавливаем пользователя и статус аутентификации
      this.setUser(response.data);
      this.setIsAuthenticated(true);

      console.log(
        "AuthStore.checkAuth: Пользователь аутентифицирован:",
        this.user
      );

      // Проверяем статус артиста у пользователя
      await this.checkArtistStatus();

      return true;
    } catch (error) {
      console.error("AuthStore.checkAuth: Ошибка при проверке токена:", error);
      console.error(
        "AuthStore.checkAuth: Детали ошибки:",
        error.response?.data || error.message
      );

      // Если токен неверный, удаляем его
      localStorage.removeItem("token");
      delete instance.defaults.headers.common["Authorization"];

      this.setIsAuthenticated(false);
      this.setUser(null);
      this.setError("Ошибка аутентификации: токен недействителен");

      return false;
    } finally {
      this.setIsLoading(false);
    }
  };

  checkArtistStatus = async () => {
    console.log(
      "AuthStore.checkArtistStatus: Проверяем статус артиста для пользователя",
      this.user?.username
    );

    if (!this.user || !this.user.email) {
      console.log(
        "AuthStore.checkArtistStatus: Нет данных пользователя или email"
      );
      this.setArtistProfile(null);
      return;
    }

    try {
      // Ищем артиста с таким же email как у пользователя
      const response = await instance.get(
        `artists/?search=${encodeURIComponent(this.user.email)}`
      );

      if (response.data && response.data.length > 0) {
        // Если найден артист, обновляем информацию пользователя
        const artist = response.data[0];
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
      } else {
        console.log("AuthStore.checkArtistStatus: Артист не найден");
        // Если артист не найден, сбрасываем профиль артиста
        this.setArtistProfile(null);

        // Обновляем только URL изображения
        this.setUser({
          ...this.user,
          img_profile_url: this.user.img_profile_url
            ? getFullImageUrl(this.user.img_profile_url)
            : null,
        });
      }
    } catch (error) {
      console.error(
        "AuthStore.checkArtistStatus: Ошибка при проверке статуса артиста:",
        error
      );
      this.setArtistProfile(null);
    }
  };

  get isArtist() {
    console.log(
      "AuthStore.isArtist: Статус артиста проверен, результат:",
      !!this.artistProfile
    );
    return !!this.artistProfile;
  }

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
