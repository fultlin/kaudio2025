import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./ErrorPage.module.scss";

const ErrorPage = ({ message, redirectTo = "/", timeout = 3000 }) => {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate(redirectTo);
    }, timeout);

    return () => clearTimeout(timer);
  }, [navigate, redirectTo, timeout]);

  return (
    <div className={styles.errorPage} role="alert" aria-live="assertive">
      <div className={styles.errorContent}>
        <h1 className={styles.errorTitle}>Ошибка</h1>
        <p className={styles.errorMessage}>{message}</p>
        <p className={styles.redirectMessage} aria-live="polite">
          Вы будете перенаправлены на главную страницу через {timeout / 1000}{" "}
          секунды...
        </p>
      </div>
    </div>
  );
};

export default ErrorPage;
