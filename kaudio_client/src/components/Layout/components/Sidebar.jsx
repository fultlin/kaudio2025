import { Link, useNavigate } from "react-router-dom";
import { observer } from "mobx-react-lite";
import authStore from "../../../stores/authStore";
import styles from "./Sidebar.module.scss";
import UploadIcon from "../../Home/components/UploadIcon";

const Sidebar = observer(() => {
  const navigate = useNavigate();
  const user = authStore.user;
  const isArtist = authStore.isArtist;

  // Обработчик клика по профилю пользователя
  const handleProfileClick = () => {
    navigate("/settings");
  };

  return (
    <div className={styles.sidebar}>
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
            <p>{isArtist ? "Артист" : "Слушатель"}</p>
          </div>
        </div>
      )}

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
        <Link to="/settings" className={styles.navLink}>
          <span className={styles.navIcon}>⚙️</span>
          <span>Настройки</span>
        </Link>
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
