import React, { useState, useEffect } from "react";
import { instance } from "../../../axios";
import styles from "./Statistics.module.scss";

const Statistics = () => {
  const [genreStats, setGenreStats] = useState([]);
  const [popularTracks, setPopularTracks] = useState([]);
  const [topArtists, setTopArtists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        setLoading(true);

        // Получаем статистику по жанрам
        const genreResponse = await instance.get("/tracks/genre_statistics/");
        setGenreStats(genreResponse.data.genre_statistics);

        // Получаем популярные треки
        const tracksResponse = await instance.get(
          "/tracks/popular_tracks/?limit=5"
        );
        setPopularTracks(tracksResponse.data.popular_tracks);

        // Получаем топ исполнителей
        const artistsResponse = await instance.get(
          "/tracks/top_artists/?limit=5"
        );
        setTopArtists(artistsResponse.data.top_artists);
      } catch (err) {
        setError("Ошибка при загрузке статистики");
        console.error("Ошибка:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatistics();
  }, []);

  if (loading) return <div>Загрузка статистики...</div>;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.statistics}>
      <div className={styles.section}>
        <h2>Статистика по жанрам</h2>
        <div className={styles.genreGrid}>
          {genreStats.map((genre, index) => (
            <div key={index} className={styles.genreCard}>
              <h3>{genre.genres__title}</h3>
              <p>Треков: {genre.tracks_count}</p>
              <p>
                Общая длительность: {Math.round(genre.total_duration / 60)} мин
              </p>
              <p>Среднее прослушиваний: {Math.round(genre.avg_play_count)}</p>
              <p>Среднее лайков: {Math.round(genre.avg_likes)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.section}>
        <h2>Популярные треки</h2>
        <div className={styles.tracksList}>
          {popularTracks.map((track, index) => (
            <div key={index} className={styles.trackCard}>
              <span className={styles.trackRank}>{index + 1}</span>
              <div className={styles.trackInfo}>
                <h3>{track.title}</h3>
                <p>{track.artist.email}</p>
              </div>
              <div className={styles.trackStats}>
                <p>Рейтинг: {track.popularity_score.toFixed(2)}</p>
                <p>Прослушиваний: {track.play_count}</p>
                <p>Лайков: {track.likes_count}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.section}>
        <h2>Топ исполнителей</h2>
        <div className={styles.artistsList}>
          {topArtists.map((artist, index) => (
            <div key={index} className={styles.artistCard}>
              <h3>{artist.artist__email}</h3>
              <p>Всего треков: {artist.total_tracks}</p>
              <p>
                Общая длительность: {Math.round(artist.total_duration / 60)} мин
              </p>
              <p>
                Средняя длительность трека:{" "}
                {Math.round(artist.avg_track_duration / 60)} мин
              </p>
              <p>Всего прослушиваний: {artist.total_plays}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Statistics;
