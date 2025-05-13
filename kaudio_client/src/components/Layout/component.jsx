import { Outlet, useNavigate } from "react-router-dom";
import styles from "./Layout.module.scss";
import authStore from "../../stores/authStore";
import { useEffect } from "react";
import { observer } from "mobx-react-lite";
import Sidebar from "./components/Sidebar";

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
    <div className={styles.container}>
      <main className={styles.main}>
        <Sidebar/>
        <Outlet />
      </main>
    </div>
  );
});

export default Layout;
