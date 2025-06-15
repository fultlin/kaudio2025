import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { observer } from "mobx-react-lite";
import searchStore from "../../stores/searchStore";
import authStore from "../../stores/authStore";
import styles from "./Search.module.scss";
import { Search as SearchIcon, Filter } from "lucide-react";
import instance from "../../axios/axios";

const Search = observer(({ variant = "header" }) => {
  const navigate = useNavigate();
  const { user } = authStore;
  const [showFilters, setShowFilters] = useState(false);
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);
  const [filters, setFilters] = useState({
    title: "",
    artist: "",
    album: "",
    genre: "",
    year: "",
    min_duration: "",
    max_duration: "",
    is_explicit: false,
    min_rating: "",
    max_rating: "",
  });

  useEffect(() => {
    // Загружаем список жанров при монтировании компонента
    const fetchGenres = async () => {
      try {
        const response = await instance.get("genres/");
        setGenres(response.data);
      } catch (error) {
        console.error("Ошибка при загрузке жанров:", error);
      }
    };
    fetchGenres();
  }, []);

  const debouncedSearch = useCallback(
    async (query, type, filters) => {
      setLoading(true);
      try {
        let url;
        switch (type.toLowerCase()) {
          case "tracks":
            url = "tracks/";
            break;
          case "albums":
            url = "albums/";
            break;
          case "artists":
            url = "artists/";
            break;
          default:
            url = "tracks/";
        }

        const params = new URLSearchParams();
        if (query) {
          params.append("search", query);
        }

        // Добавляем фильтры
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== "" && value !== false) {
            params.append(key, value);
          }
        });

        const response = await instance.get(`${url}?${params}`);
        if (response.status === 200) {
          navigate(
            `/search?q=${encodeURIComponent(
              query
            )}&type=${type.toLowerCase()}&${params.toString()}`
          );
        }
      } catch (error) {
        console.error("Ошибка при поиске:", error);
      } finally {
        setLoading(false);
      }
    },
    [navigate]
  );

  const handleSearch = (e) => {
    e.preventDefault();
    const query = e.target.value;
    searchStore.setSearchQuery(query);

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    const newTimeoutId = setTimeout(() => {
      debouncedSearch(query, searchStore.searchType, filters);
    }, 500);

    setTimeoutId(newTimeoutId);
  };

  const handleFilterChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === "checkbox" ? checked : value;
    setFilters((prev) => ({
      ...prev,
      [name]: newValue,
    }));
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    debouncedSearch(searchStore.searchQuery, searchStore.searchType, filters);
  };

  const resetFilters = () => {
    setFilters({
      title: "",
      artist: "",
      album: "",
      genre: "",
      year: "",
      min_duration: "",
      max_duration: "",
      is_explicit: false,
      min_rating: "",
      max_rating: "",
    });
  };

  if (variant === "sidebar") {
    return (
      <div className={styles.sidebarSearch}>
        <form onSubmit={handleSearch}>
          <input
            type="text"
            className={styles.sidebarSearchInput}
            placeholder="Поиск..."
            value={searchStore.searchQuery}
            onChange={(e) => searchStore.setSearchQuery(e.target.value)}
          />
          <button type="submit" className={styles.sidebarSearchButton}>
            <SearchIcon className={styles.searchIcon} />
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className={`${styles.searchContainer} ${styles[variant]}`}>
      <form onSubmit={handleFilterSubmit} className={styles.searchForm}>
        <div className={styles.searchInputContainer}>
          <SearchIcon className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Поиск..."
            onChange={handleSearch}
            className={styles.searchInput}
          />
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={styles.filterButton}
          >
            <Filter />
          </button>
        </div>

        {showFilters && (
          <div className={styles.filtersPanel}>
            <div className={styles.filterGroup}>
              <input
                type="text"
                name="title"
                placeholder="Название"
                value={filters.title}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
              <input
                type="text"
                name="artist"
                placeholder="Исполнитель"
                value={filters.artist}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
              <input
                type="text"
                name="album"
                placeholder="Альбом"
                value={filters.album}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
            </div>

            <div className={styles.filterGroup}>
              <select
                name="genre"
                value={filters.genre}
                onChange={handleFilterChange}
                className={styles.filterSelect}
              >
                <option value="">Все жанры</option>
                {genres.map((genre) => (
                  <option key={genre.id} value={genre.id}>
                    {genre.title}
                  </option>
                ))}
              </select>
              <input
                type="number"
                name="year"
                placeholder="Год"
                value={filters.year}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
            </div>

            <div className={styles.filterGroup}>
              <input
                type="number"
                name="min_duration"
                placeholder="Мин. длительность (сек)"
                value={filters.min_duration}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
              <input
                type="number"
                name="max_duration"
                placeholder="Макс. длительность (сек)"
                value={filters.max_duration}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
            </div>

            <div className={styles.filterGroup}>
              <input
                type="number"
                name="min_rating"
                placeholder="Мин. рейтинг"
                value={filters.min_rating}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
              <input
                type="number"
                name="max_rating"
                placeholder="Макс. рейтинг"
                value={filters.max_rating}
                onChange={handleFilterChange}
                className={styles.filterInput}
              />
            </div>

            <div className={styles.filterGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="is_explicit"
                  checked={filters.is_explicit}
                  onChange={handleFilterChange}
                />
                Только с ненормативной лексикой
              </label>
            </div>

            <div className={styles.filterActions}>
              <button type="submit" className={styles.applyButton}>
                Применить
              </button>
              <button
                type="button"
                onClick={resetFilters}
                className={styles.resetButton}
              >
                Сбросить
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
});

export default Search;
