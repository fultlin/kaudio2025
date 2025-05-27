import { Outlet, useNavigate } from "react-router-dom";
import styles from "./Layout.module.scss";
import authStore from "../../stores/authStore";
import { useEffect, useState } from "react";
import { observer } from "mobx-react-lite";
import Sidebar from "./components/Sidebar";
import MiniPlayer from "../MiniPlayer/component";
import { FaBars } from "react-icons/fa";

const Layout = observer(() => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    authStore.checkAuth();
  }, []);

  const handleLogout = () => {
    authStore.logout();
    navigate("/auth");
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <button
          className={styles.menuButton}
          onClick={toggleSidebar}
          aria-label="Открыть меню"
        >
          <FaBars />
        </button>

        <div
          className={`${styles.sidebarOverlay} ${
            isSidebarOpen ? styles.visible : ""
          }`}
          onClick={closeSidebar}
        />

        <Sidebar isOpen={isSidebarOpen} />

        <div className={styles.content}>
          <Outlet />
        </div>
      </main>
    </div>
  );
});

export default Layout;
