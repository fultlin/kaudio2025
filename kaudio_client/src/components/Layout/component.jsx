import { Outlet, useNavigate } from "react-router-dom";
import Header from "./components/Header/components";
import styles from "./Layout.module.scss";
import authStore from "../../stores/authStore";
import { useEffect } from "react";
import { observer } from "mobx-react-lite";

const Layout = observer(() => {
  const navigate = useNavigate();

  useEffect(() => {
    authStore.checkAuth();
  }, []);

  const handleLogout = () => {
    authStore.logout();
    navigate("/auth");
  };

  return (
    <>
      <Header auth={authStore.isAuthenticated} onLogout={handleLogout} />
      <main className={styles.main}>
        <div className={styles.wrapper}>
          <Outlet />
        </div>
      </main>
    </>
  );
});

export default Layout;
