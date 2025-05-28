import { NavLink, Link } from "react-router-dom";
import styles from "./Header.module.scss";
import { observer } from "mobx-react-lite";
import Search from "../../../Search/component";
import authStore from "../../../../stores/authStore";
import { useState, useRef, useEffect } from "react";
import {
  getFullImageUrl,
  getAvatarInitial,
} from "../../../../utils/imageUtils";
import Avatar from "../../../UI/Avatar/component";
import { useNavigate } from "react-router-dom";

const Header = observer(({ auth, onLogout }) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [uploadMenuOpen, setUploadMenuOpen] = useState(false);
  const dropdownRef = useRef(null);
  const uploadMenuRef = useRef(null);
  const navigate = useNavigate();

  // Закрываем выпадающие меню при клике вне
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
      if (
        uploadMenuRef.current &&
        !uploadMenuRef.current.contains(event.target)
      ) {
        setUploadMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <header className={styles.header} role="banner">
      <a href="#main-content" className={styles.skipLink}>
        Перейти к основному содержимому
      </a>
      <div className={styles.wrapper}>
        <nav
          className={styles.navigation}
          role="navigation"
          aria-label="Основная навигация"
        >
          <div className={styles.leftNav}>
            <NavLink
              to="/"
              className={styles.logo}
              aria-label="Главная страница Kaudio"
            >
              Kaudio
            </NavLink>

            {auth && (
              <ul className={styles.navLinks}>
                <li>
                  <NavLink
                    to="/"
                    className={({ isActive }) =>
                      isActive
                        ? `${styles.navLink} ${styles.active}`
                        : styles.navLink
                    }
                    aria-current={({ isActive }) =>
                      isActive ? "page" : undefined
                    }
                  >
                    Главная
                  </NavLink>
                </li>
                <li>
                  <NavLink
                    to="/music"
                    className={({ isActive }) =>
                      isActive
                        ? `${styles.navLink} ${styles.active}`
                        : styles.navLink
                    }
                    aria-current={({ isActive }) =>
                      isActive ? "page" : undefined
                    }
                  >
                    Музыка
                  </NavLink>
                </li>
                {authStore.isArtist && (
                  <li
                    className={styles.uploadMenuContainer}
                    ref={uploadMenuRef}
                  >
                    <button
                      className={styles.uploadButton}
                      onClick={() => setUploadMenuOpen(!uploadMenuOpen)}
                    >
                      Загрузить <span className={styles.arrowIcon}>▼</span>
                    </button>

                    {uploadMenuOpen && (
                      <div className={styles.uploadMenu}>
                        <NavLink
                          to="/upload/track"
                          className={styles.uploadMenuItem}
                          onClick={() => setUploadMenuOpen(false)}
                        >
                          Загрузить трек
                        </NavLink>
                        <NavLink
                          to="/upload/album"
                          className={styles.uploadMenuItem}
                          onClick={() => setUploadMenuOpen(false)}
                        >
                          Загрузить альбом
                        </NavLink>
                      </div>
                    )}
                  </li>
                )}
              </ul>
            )}
          </div>

          <div className={styles.centerNav}>
            <Search />
          </div>

          <div className={styles.rightNav}>
            {auth ? (
              <div className={styles.userMenu} ref={dropdownRef}>
                <button
                  className={styles.userButton}
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                >
                  <span className={styles.userName}>
                    {authStore.user?.username || "Пользователь"}
                  </span>
                  <Avatar
                    imageUrl={authStore.user?.img_profile_url}
                    username={authStore.user?.username}
                    size="sm"
                    className={styles.headerAvatar}
                  />
                </button>

                {dropdownOpen && (
                  <div className={styles.dropdown}>
                    <NavLink
                      to="/settings"
                      className={styles.dropdownItem}
                      onClick={() => setDropdownOpen(false)}
                    >
                      Настройки профиля
                    </NavLink>
                    <button
                      onClick={() => {
                        onLogout();
                        setDropdownOpen(false);
                      }}
                      className={styles.dropdownItem}
                    >
                      Выйти
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.authButtons}>
                <Link to="/auth" className={styles.loginButton}>
                  Войти
                </Link>
                <Link to="/register" className={styles.registerButton}>
                  Регистрация
                </Link>
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
});

export default Header;
