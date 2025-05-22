import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const ErrorPage = ({ message, redirectTo = "/", timeout = 3000 }) => {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate(redirectTo);
    }, timeout);

    return () => clearTimeout(timer);
  }, [navigate, redirectTo, timeout]);

  return (
    <div className="error-page">
      <h2>Ошибка</h2>
      <p>{message}</p>
      <p>
        Вы будете перенаправлены на главную страницу через {timeout / 1000}{" "}
        секунды...
      </p>
    </div>
  );
};

export default ErrorPage;
