import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Search.module.scss";
import homeStore from "stores/homeStore";
import instance from "../../axios/axios";

export default function Search({ isSidebar = false }) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchType, setSearchType] = useState("all"); // all, title, artist, username

  // Состояния для расширенного поиска
  const [searchFilters, setSearchFilters] = useState({
    title: "",
    artist: "",
    album: "",
    genre: "",
    year: "",
  });
  const [genres, setGenres] = useState([]);
  const [years, setYears] = useState([]);

  useEffect(() => {
    if (showAdvanced) {
      // Загрузка жанров и годов только при открытии расширенного поиска
      const fetchGenres = async () => {
        try {
          const response = await instance.get("/genres/");
          setGenres(response.data);
        } catch (error) {
          console.error("Ошибка при загрузке жанров:", error);
        }
      };

      const currentYear = new Date().getFullYear();
      const yearsList = Array.from(
        { length: 50 },
        (_, index) => currentYear - index
      );
      setYears(yearsList);

      fetchGenres();
    }
  }, [showAdvanced]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    let queryParams = new URLSearchParams();

    switch (searchType) {
      case "title":
        queryParams.append("title", searchQuery);
        break;
      case "artist":
        queryParams.append("artist", searchQuery);
        break;
      case "username":
        queryParams.append("username", searchQuery);
        break;
      case "all":
      default:
        queryParams.append("q", searchQuery);
        break;
    }

    navigate(`/search?${queryParams.toString()}`);
  };

  if (isSidebar) {
    return (
      <div className={styles.sidebarSearch}>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Поиск..."
            className={styles.sidebarSearchInput}
          />
          <button type="submit" className={styles.sidebarSearchButton}>
            <svg
              fill="white"
              height="20px"
              width="20px"
              viewBox="0 0 488.4 488.4"
              className={styles.searchIcon}
            >
              <path
                d="M0,203.25c0,112.1,91.2,203.2,203.2,203.2c51.6,0,98.8-19.4,134.7-51.2l129.5,129.5c2.4,2.4,5.5,3.6,8.7,3.6
                s6.3-1.2,8.7-3.6c4.8-4.8,4.8-12.5,0-17.3l-129.6-129.5c31.8-35.9,51.2-83,51.2-134.7c0-112.1-91.2-203.2-203.2-203.2
                S0,91.15,0,203.25z M381.9,203.25c0,98.5-80.2,178.7-178.7,178.7s-178.7-80.2-178.7-178.7s80.2-178.7,178.7-178.7
                S381.9,104.65,381.9,203.25z"
              />
            </svg>
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className={styles.searchContainer}>
      <form onSubmit={handleSubmit} className={styles.searchForm}>
        <div className={styles.searchTypeSelector}>
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className={styles.searchTypeSelect}
          >
            <option value="all">Везде</option>
            <option value="title">По названию</option>
            <option value="artist">По исполнителю</option>
            <option value="username">По нику</option>
          </select>
        </div>
        <div className={styles.searchInputWrapper}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Что хотите послушать?"
            className={styles.searchInput}
          />
          <button type="submit" className={styles.searchButton}>
            Поиск
          </button>
        </div>
      </form>
    </div>
  );
}
