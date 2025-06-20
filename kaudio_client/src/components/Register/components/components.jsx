import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import authStore from "../../../stores/authStore";
import styles from "./Register.module.scss";
import GoogleLoginButton from "../../Login/GoogleLoginButton";

const Form = () => {
  const [formData, setFormData] = useState({
    login: "",
    email: "",
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
      const success = await authStore.register({
        username: formData.login,
        email: formData.email,
        password: formData.password,
      });

      if (success) {
        navigate("/auth");
      } else {
        setError(authStore.error);
      }
    } catch (error) {
      setError("Ошибка при регистрации");
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      <h2 className={styles.title}>Регистрация</h2>

      {error && <div className={styles.error}>{error}</div>}

      <label>
        Логин:
        <input
          type="text"
          name="login"
          value={formData.login}
          onChange={handleChange}
          className={styles.input}
          required
        />
      </label>
      <br />

      <label>
        Email:
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className={styles.input}
          required
        />
      </label>
      <br />

      <label>
        Пароль:
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
        {authStore.loading ? "Загрузка..." : "Зарегистрироваться"}
      </button>
      <div style={{ marginTop: 24 }}>
        <GoogleLoginButton />
      </div>
    </form>
  );
};

export default Form;
