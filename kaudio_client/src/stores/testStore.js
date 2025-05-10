import { makeAutoObservable } from "mobx";
import examplar from "../axios/axios";
import { jwtDecode } from "jwt-decode";

class TestStore {
  token = "";
  isAuthenticated = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
  }

  checkAuth = async () => {
    this.token = window.localStorage.getItem("token");

    if (this.token) {
      try {
        const response = await examplar
          .get(`users/auth/${this.token}`)
          .then((res) => {
            this.setAuth(true);
            const decodedToken = jwtDecode(this.token);
            return decodedToken; // Вернуть правильный объект, содержащий логин
          });
      } catch (error) {
        this.setAuth(false);
        this.error = error.response;
        console.error("Ошибка при аутентификации:", this.error);
      }
    } else {
      this.setAuth(false);
    }
  };

  setAuth = (authStatus) => {
    this.isAuthenticated = authStatus;
  };

  logout = () => {
    window.localStorage.removeItem("token");
    window.localStorage.removeItem("login");
    this.setAuth(false);
    console.log("User logged out");
  };
}

const newTestStore = new TestStore();
export default newTestStore;
