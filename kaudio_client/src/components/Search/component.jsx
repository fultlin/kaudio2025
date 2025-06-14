import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { observer } from "mobx-react-lite";
import searchStore from "../../stores/searchStore";
import authStore from "../../stores/authStore";
import styles from "./Search.module.scss";
import { Search as SearchIcon } from "lucide-react";
import instance from "../../axios/axios";

const Search = observer(({ variant = "header" }) => {
  const navigate = useNavigate();
  const { user } = authStore;
  const [showFilters, setShowFilters] = useState(false);
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);

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
          if (value) {
            params.append(key, value);
          }
        });

        const response = await instance.get(`${url}?${params}`);
        if (response.status === 200) {
          navigate(
            `/search?q=${encodeURIComponent(query)}&type=${type.toLowerCase()}`
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
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    const newTimeoutId = setTimeout(() => {
      debouncedSearch(
        searchStore.searchQuery,
        searchStore.searchType,
        searchStore.filters
      );
    }, 300);
    setTimeoutId(newTimeoutId);
  };

  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [timeoutId]);

  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const response = await instance.get("genres/");
        if (response.status === 200) {
          setGenres(response.data);
        }
      } catch (error) {
        console.error("Ошибка при загрузке жанров:", error);
      }
    };

    fetchGenres();
  }, []);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    searchStore.setFilters({
      ...searchStore.filters,
      [name]: value,
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
    <div className={styles.searchContainer}>
      <form onSubmit={handleSearch} className={styles.searchForm}>
        <div className={styles.searchTypeSelector}>
          <select
            className={styles.searchTypeSelect}
            value={searchStore.searchType}
            onChange={(e) => searchStore.setSearchType(e.target.value)}
          >
            <option value="tracks">Треки</option>
            <option value="albums">Альбомы</option>
            <option value="artists">Исполнители</option>
          </select>
        </div>

        <div className={styles.searchInputWrapper}>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Поиск..."
            value={searchStore.searchQuery}
            onChange={(e) => searchStore.setSearchQuery(e.target.value)}
          />
          <button
            type="submit"
            className={styles.searchButton}
            disabled={loading}
          >
            {loading ? "Поиск..." : "Найти"}
          </button>
        </div>

        {showFilters && (
          <div className={styles.searchFilters}>
            <div className={styles.filterRow}>
              <select
                name="genre"
                className={styles.filterSelect}
                value={searchStore.filters.genre || ""}
                onChange={handleFilterChange}
              >
                <option value="">Все жанры</option>
                {genres.map((genre) => (
                  <option key={genre.id} value={genre.id}>
                    {genre.name}
                  </option>
                ))}
              </select>

              <input
                type="text"
                name="artist"
                className={styles.filterInput}
                placeholder="Исполнитель"
                value={searchStore.filters.artist || ""}
                onChange={handleFilterChange}
              />
            </div>

            {searchStore.searchType === "albums" && (
              <div className={styles.filterRow}>
                <input
                  type="text"
                  name="album"
                  className={styles.filterInput}
                  placeholder="Название альбома"
                  value={searchStore.filters.album || ""}
                  onChange={handleFilterChange}
                />
                <input
                  type="date"
                  name="release_date"
                  className={styles.filterInput}
                  value={searchStore.filters.release_date || ""}
                  onChange={handleFilterChange}
                />
              </div>
            )}
          </div>
        )}
      </form>
    </div>
  );
});

export default Search;
