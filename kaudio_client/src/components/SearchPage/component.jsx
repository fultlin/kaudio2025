// kaudio_client/src/components/SearchPage/component.jsx
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { observer } from "mobx-react-lite";
import playerStore from "../../stores/playerStore";
import instance from "../../axios/axios";
import styles from "./SearchPage.module.scss";
import MiniPlayer from "../MiniPlayer/component";

const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
};

const SearchPage = observer(() => {
  const [searchParams] = useSearchParams();
  const [searchResults, setSearchResults] = useState({
    tracks: [],
    artists: [],
  });

  const fetchResults = async () => {
    const query = searchParams.get("q");
    if (!query) return;

    try {
      const [tracksRes, artistsRes] = await Promise.all([
        instance.get(`/tracks/`, {
          params: {
            search: query,
          },
        }),
        instance.get(`/artists/`, {
          params: {
            search: query,
          },
        }),
      ]);

      setSearchResults({
        tracks: Array.isArray(tracksRes.data) ? tracksRes.data : [],
        artists: Array.isArray(artistsRes.data) ? artistsRes.data : [],
      });
    } catch (error) {
      console.error("Ошибка при поиске:", error);
      setSearchResults({
        tracks: [],
        artists: [],
      });
    }
  };

  useEffect(() => {
    fetchResults();
  }, [searchParams]);

  const handlePlayTrack = (track) => {
    if (playerStore.trackId === track.id) {
      if (playerStore.isPlaying) {
        playerStore.pause();
      } else {
        playerStore.play();
      }
    } else {
      playerStore.loadTrack(track, 0, searchResults.tracks);
    }
  };

  return (
    <div className={styles.searchPage}>
      <h2>Результаты поиска для: {searchParams.get("q")}</h2>

      {/* Секция артистов */}
      {searchResults.artists.length > 0 && (
        <div className={styles.section}>
          <h3>Исполнители</h3>
          <div className={styles.artistResults}>
            {searchResults.artists.map((artist) => (
              <div key={artist.id} className={styles.artistItem}>
                <img
                  src={artist.cover_image || "/default-artist.png"}
                  alt={
                    artist.user
                      ? artist.user.username
                      : "Неизвестный исполнитель"
                  }
                  className={styles.artistImage}
                />
                <div className={styles.artistInfo}>
                  <h4>
                    {artist.user
                      ? artist.user.username
                      : "Неизвестный исполнитель"}
                  </h4>
                  {artist.is_verified && (
                    <span className={styles.verifiedBadge}>✓</span>
                  )}
                  <p>{artist.monthly_listeners} слушателей</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Секция треков */}
      {searchResults.tracks.length > 0 && (
        <div className={styles.section}>
          <h3>Треки</h3>
          <div className={styles.trackResults}>
            {searchResults.tracks.map((track) => (
              <div key={track.id} className={styles.trackItem}>
                <div className={styles.trackInfo}>
                  <h4>{track.title}</h4>
                  <p>
                    {track.artist?.user?.username ||
                      track.artist?.email ||
                      "Неизвестный исполнитель"}
                  </p>
                  <p>{formatDuration(track.duration)}</p>
                </div>
                <button
                  onClick={() => handlePlayTrack(track)}
                  className={styles.playButton}
                >
                  {playerStore.trackId === track.id && playerStore.isPlaying
                    ? "⏸"
                    : "▶"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Сообщение, если ничего не найдено */}
      {!searchResults.tracks.length && !searchResults.artists.length && (
        <div className={styles.noResults}>
          <p>По вашему запросу ничего не найдено</p>
        </div>
      )}

      {/* Добавляем MiniPlayer */}
      <div className={styles.miniPlayerWrapper}>
        <MiniPlayer
          name={playerStore.trackUrl}
          isPlaying={playerStore.isPlaying}
          onPlayPause={() => {
            if (playerStore.isPlaying) {
              playerStore.pause();
            } else {
              playerStore.play();
            }
          }}
          onPrev={() => playerStore.prevTrack()}
          onNext={() => playerStore.nextTrack()}
          trackName={playerStore.trackName}
          author={playerStore.author}
        />
      </div>
    </div>
  );
});

export default SearchPage;
