import React, { useState, useEffect } from "react";
import instance from "../../../axios/axios";
import styles from "./Statistics.module.scss";

const Statistics = () => {
  const [genreStats, setGenreStats] = useState([]);
  const [popularTracks, setPopularTracks] = useState([]);
  const [topArtists, setTopArtists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);

  const fetchStatistics = async () => {
    try {
      setLoading(true);

      // Получаем статистику по жанрам
      const genreResponse = await instance.get("tracks/genre-statistics");
      setGenreStats(genreResponse.data.genre_statistics);

      // Получаем популярные треки
      const tracksResponse = await instance.get(
        "tracks/popular-tracks?limit=5"
      );
      console.log(
        "Данные популярных треков:",
        tracksResponse.data.popular_tracks
      );
      setPopularTracks(tracksResponse.data.popular_tracks);

      // Получаем топ исполнителей
      const artistsResponse = await instance.get("tracks/top-artists?limit=5");
      setTopArtists(artistsResponse.data.top_artists);
    } catch (err) {
      setError("Ошибка при загрузке статистики");
      console.error("Ошибка:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatistics();

    // Обновляем статистику каждые 5 минут
    const interval = setInterval(fetchStatistics, 5 * 60 * 1000);
    setRefreshInterval(interval);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
      return `${hours} ч ${minutes} мин`;
    }
    return `${minutes} мин`;
  };

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner}></div>
        <p>Загрузка статистики...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.error}>
        <h3>Ошибка загрузки</h3>
        <p>{error}</p>
        <button onClick={fetchStatistics} className={styles.retryButton}>
          Попробовать снова
        </button>
      </div>
    );
  }

  return (
    <div className={styles.statistics}>
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2>Статистика по жанрам</h2>
          <span className={styles.count}>{genreStats.length} жанров</span>
        </div>
        <div className={styles.genreGrid}>
          {genreStats.map((genre, index) => (
            <div key={index} className={styles.genreCard}>
              <h3>{genre.genres__title}</h3>
              <div className={styles.statItem}>
                <span className={styles.label}>Треков:</span>
                <span className={styles.value}>{genre.tracks_count}</span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.label}>Общая длительность:</span>
                <span className={styles.value}>
                  {formatDuration(genre.total_duration)}
                </span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.label}>Среднее прослушиваний:</span>
                <span className={styles.value}>
                  {Math.round(genre.avg_play_count)}
                </span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.label}>Среднее лайков:</span>
                <span className={styles.value}>
                  {Math.round(genre.avg_likes)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2>Популярные треки</h2>
          <button onClick={fetchStatistics} className={styles.refreshButton}>
            Обновить
          </button>
        </div>
        <div className={styles.tracksList}>
          {popularTracks.map((track, index) => (
            <div key={index} className={styles.trackCard}>
              <span className={styles.trackRank}>{index + 1}</span>
              <div className={styles.trackInfo}>
                <h3>{track.title}</h3>
                <p>{track.artist__email}</p>
              </div>
              <div className={styles.trackStats}>
                <div className={styles.statItem}>
                  <span className={styles.label}>Рейтинг:</span>
                  <span className={styles.value}>
                    {track.popularity_score.toFixed(2)}
                  </span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.label}>Прослушиваний:</span>
                  <span className={styles.value}>{track.play_count}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.label}>Лайков:</span>
                  <span className={styles.value}>{track.likes_count}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2>Топ исполнителей</h2>
          <span className={styles.count}>{topArtists.length} исполнителей</span>
        </div>
        <div className={styles.artistsList}>
          {topArtists.map((artist, index) => (
            <div key={index} className={styles.artistCard}>
              <div className={styles.artistRank}>#{index + 1}</div>
              <h3>{artist.artist__email}</h3>
              <div className={styles.statItem}>
                <span className={styles.label}>Всего треков:</span>
                <span className={styles.value}>{artist.total_tracks}</span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.label}>Общая длительность:</span>
                <span className={styles.value}>
                  {formatDuration(artist.total_duration)}
                </span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.label}>
                  Средняя длительность трека:
                </span>
                <span className={styles.value}>
                  {formatDuration(artist.avg_track_duration)}
                </span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.label}>Всего прослушиваний:</span>
                <span className={styles.value}>{artist.total_plays}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Statistics;
