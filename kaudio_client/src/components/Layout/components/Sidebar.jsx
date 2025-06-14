import { Link, useNavigate } from "react-router-dom";
import { observer } from "mobx-react-lite";
import authStore from "../../../stores/authStore";
import styles from "./Sidebar.module.scss";
import UploadIcon from "../../Home/components/UploadIcon";
import Search from "../../Search/component";

const Sidebar = observer(({ isOpen }) => {
  const navigate = useNavigate();
  const user = authStore.user;
  const isArtist = authStore.isArtist;
  const isAdmin = authStore.isAdmin;

  const handleProfileClick = () => {
    navigate("/profile");
  };

  const handleLogout = () => {
    authStore.logout();
    navigate("/auth");
  };

  return (
    <div className={`${styles.sidebar} ${isOpen ? styles.open : ""}`}>
      <div className={styles.sidebarHeader}>
        <h2>KAudio</h2>
      </div>

      {user && (
        <div className={styles.userProfile} onClick={handleProfileClick}>
          <div className={styles.profileImage}>
            {user.img_profile_url ? (
              <img src={user.img_profile_url} alt={user.username} />
            ) : (
              <div className={styles.defaultAvatar}>
                {user.username.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
          <div className={styles.profileInfo}>
            <h3>{user.username}</h3>
            <p>
              {isAdmin ? "Администратор" : isArtist ? "Артист" : "Слушатель"}
            </p>
          </div>
        </div>
      )}

      <Search isSidebar={true} />
      <nav className={styles.sidebarNav}>
        <Link to="/" className={styles.navLink}>
          <span className={styles.navIcon}>🏠</span>
          <span>Главная</span>
        </Link>
        <Link to="/music" className={styles.navLink}>
          <span className={styles.navIcon}>🎵</span>
          <span>Моя музыка</span>
        </Link>
        <Link to="/playlists" className={styles.navLink}>
          <span className={styles.navIcon}>📑</span>
          <span>Плейлисты</span>
        </Link>
        <Link to="/statistics" className={styles.navLink}>
          <span className={styles.navIcon}>📊</span>
          <span>Статистика</span>
        </Link>
        <Link to="/settings" className={styles.navLink}>
          <span className={styles.navIcon}>⚙️</span>
          <span>Настройки</span>
        </Link>
        <button onClick={handleLogout} className={styles.navLink}>
          <span className={styles.navIcon}>🚪</span>
          <span>Выйти</span>
        </button>
      </nav>

      <div className={styles.uploadWrapper}>
        <Link to="/upload" className={styles.uploadButton}>
          <UploadIcon />
          <span>Загрузить</span>
        </Link>
        <Link
          to="/upload/album"
          className={styles.uploadButton}
          style={{ marginTop: "10px" }}
        >
          <span className={styles.navIcon}>💿</span>
          <span>Загрузить альбом</span>
        </Link>
      </div>
    </div>
  );
});

export default Sidebar;
