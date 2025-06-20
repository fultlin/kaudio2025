import React, { useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { observer } from "mobx-react-lite";
import authStore from "../../stores/authStore";
import styles from "./Login.module.scss";
import GoogleLoginButton from "./GoogleLoginButton";

const LoginForm = observer(() => {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);

    try {
      const success = await authStore.login(
        formData.username,
        formData.password
      );

      if (success) {
        navigate("/");
      } else {
        setError(authStore.error);
      }
    } catch (error) {
      setError("Ошибка авторизации");
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className={styles.form}>
        <h2 className={styles.login__form}>Авторизация</h2>

        {error && <div className={styles.error}>{error}</div>}

        <label>
          Имя пользователя:
          <br />
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            className={styles.input}
            required
          />
        </label>
        <br />

        <label>
          Пароль:
          <br />
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={styles.input}
            required
          />
        </label>
        <br />

        <button
          type="submit"
          className={styles.button}
          disabled={authStore.loading}
        >
          {authStore.loading ? "Загрузка..." : "Войти"}
        </button>

        <span>
          <NavLink to="/register" className={styles.register__link}>
            Регистрация
          </NavLink>
        </span>
        <div className={styles.google__login}>
          <GoogleLoginButton />
        </div>
      </form>
    </>
  );
});

export default LoginForm;
