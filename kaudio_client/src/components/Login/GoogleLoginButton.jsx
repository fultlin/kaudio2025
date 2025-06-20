import React from "react";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";
import axios from "../../axios/axios";
import { useNavigate } from "react-router-dom";
import authStore from "../../stores/authStore";

const GOOGLE_CLIENT_ID =
  "735027786085-v9i01gi29or2lauqhisufj51a522fuph.apps.googleusercontent.com";

const GoogleLoginButton = () => {
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse) => {
    try {
      const access_token = credentialResponse.credential;
      const response = await axios.post("/auth/social-login/", {
        provider: "google",
        access_token,
      });
      console.log("Ответ сервера:", response.data);
      if (response.data && response.data.token) {
        localStorage.setItem("token", response.data.token);
        axios.defaults.headers.common[
          "Authorization"
        ] = `Token ${response.data.token}`;
        await authStore.checkAuth();
        navigate("/");
      } else {
        alert("Ошибка авторизации через Google");
      }
    } catch (error) {
      alert(
        "Ошибка входа через Google: " +
          (error.response?.data?.detail || error.message)
      );
    }
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => alert("Ошибка Google авторизации")}
        useOneTap
      />
    </GoogleOAuthProvider>
  );
};

export default GoogleLoginButton;
