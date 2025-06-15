// kaudio_client/src/components/SearchPage/component.jsx
import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { observer } from "mobx-react-lite";
import playerStore from "../../stores/playerStore";
import instance from "../../axios/axios";
import styles from "./SearchPage.module.scss";
import MiniPlayer from "../MiniPlayer/component";
import { ArrowRight } from "lucide-react";

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
    albums: [],
    playlists: [],
    userActivities: [],
  });
  const navigate = useNavigate();

  const fetchResults = async () => {
    const query = searchParams.get("q");
    const type = searchParams.get("type") || "tracks";

    const filters = {};
    for (const [key, value] of searchParams.entries()) {
      if (key !== "q" && key !== "type") {
        filters[key] = value;
      }
    }

    if (!query && Object.keys(filters).length === 0) {
      setSearchResults({
        tracks: [],
        artists: [],
        albums: [],
        playlists: [],
        userActivities: [],
      });
      return;
    }

    try {
      let tracksRes = { data: [] };
      let artistsRes = { data: [] };
      let albumsRes = { data: [] };
      let playlistsRes = { data: [] };
      let userActivitiesRes = { data: [] };

      if (type === "tracks" || type === "all") {
        tracksRes = await instance.get(`/tracks/`, {
          params: {
            search: query,
            ...filters,
          },
        });
      }
      if (type === "artists" || type === "all") {
        artistsRes = await instance.get(`/artists/`, {
          params: {
            search: query,
            ...filters,
          },
        });
      }
      if (type === "albums" || type === "all") {
        albumsRes = await instance.get(`/albums/`, {
          params: {
            search: query,
            ...filters,
          },
        });
      }
      if (type === "playlists" || type === "all") {
        playlistsRes = await instance.get(`/playlists/`, {
          params: {
            search: query,
            ...filters,
          },
        });
      }
      if (type === "user_activities" || type === "all") {
        userActivitiesRes = await instance.get(`/user-activities/`, {
          params: {
            search: query,
            ...filters,
          },
        });
      }

      setSearchResults({
        tracks: Array.isArray(tracksRes.data) ? tracksRes.data : [],
        artists: Array.isArray(artistsRes.data) ? artistsRes.data : [],
        albums: Array.isArray(albumsRes.data) ? albumsRes.data : [],
        playlists: Array.isArray(playlistsRes.data) ? playlistsRes.data : [],
        userActivities: Array.isArray(userActivitiesRes.data)
          ? userActivitiesRes.data
          : [],
      });
    } catch (error) {
      console.error("Ошибка при поиске:", error);
      setSearchResults({
        tracks: [],
        artists: [],
        albums: [],
        playlists: [],
        userActivities: [],
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

  const handlePlayAlbum = (album) => {
    if (album.tracks && album.tracks.length > 0) {
      handlePlayTrack(album.tracks[0]);
    }
  };

  const handlePlayPlaylist = (playlist) => {
    if (playlist.tracks && playlist.tracks.length > 0) {
      handlePlayTrack(playlist.tracks[0]);
    }
  };

  const handleGoToTrack = (trackId) => {
    navigate(`/tracks/${trackId}`);
  };

  const handleGoToAlbum = (albumId) => {
    navigate(`/albums/${albumId}`);
  };

  const handleGoToArtist = (artistId) => {
    navigate(`/artist/${artistId}`);
  };

  const handleGoToPlaylist = (playlistId) => {
    navigate(`/playlists/${playlistId}`);
  };

  return (
    <div className={styles.searchPage}>
      <h2>Результаты поиска для: {searchParams.get("q") || ""}</h2>

      {/* Секция артистов */}
      {searchResults.artists.length > 0 && (
        <div className={styles.section}>
          <h3>Исполнители</h3>
          <div className={styles.artistResults}>
            {searchResults.artists.map((artist) => (
              <div
                key={artist.id}
                className={styles.artistItem}
                onClick={() => handleGoToArtist(artist.id)}
              >
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
                  <div className={styles.trackDuration}>
                    {formatDuration(track.duration)}
                  </div>
                </div>
                <div
                  className={styles.trackGoTo}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleGoToTrack(track.id);
                  }}
                  title="Перейти на страницу трека"
                >
                  <ArrowRight size={20} />
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

      {/* Секция альбомов */}
      {searchResults.albums.length > 0 && (
        <div className={styles.section}>
          <h3>Альбомы</h3>
          <div className={styles.albumResults}>
            {searchResults.albums.map((album) => (
              <div
                key={album.id}
                className={styles.albumItem}
                onClick={() => handleGoToAlbum(album.id)}
              >
                <img
                  src={album.cover_image || "/default-album.png"}
                  alt={album.title}
                  className={styles.albumImage}
                />
                <div className={styles.albumInfo}>
                  <h4>{album.title}</h4>
                  <p>
                    {album.artist?.user?.username ||
                      album.artist?.email ||
                      "Неизвестный исполнитель"}
                  </p>
                  <p>{album.release_date}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlayAlbum(album);
                  }}
                  className={styles.playButton}
                >
                  ▶
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Секция плейлистов */}
      {searchResults.playlists.length > 0 && (
        <div className={styles.section}>
          <h3>Плейлисты</h3>
          <div className={styles.playlistResults}>
            {searchResults.playlists.map((playlist) => (
              <div
                key={playlist.id}
                className={styles.playlistItem}
                onClick={() => handleGoToPlaylist(playlist.id)}
              >
                <img
                  src={playlist.cover_image || "/default-playlist.png"}
                  alt={playlist.title}
                  className={styles.playlistImage}
                />
                <div className={styles.playlistInfo}>
                  <h4>{playlist.title}</h4>
                  <p>{playlist.user?.username || "Неизвестный пользователь"}</p>
                  <p>{playlist.total_tracks} треков</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlayPlaylist(playlist);
                  }}
                  className={styles.playButton}
                >
                  ▶
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Секция активности пользователей */}
      {searchResults.userActivities.length > 0 && (
        <div className={styles.section}>
          <h3>Активности пользователей</h3>
          <div className={styles.activityResults}>
            {searchResults.userActivities.map((activity) => (
              <div key={activity.id} className={styles.activityItem}>
                <p>Пользователь: {activity.user?.username}</p>
                <p>Тип активности: {activity.activity_type}</p>
                {activity.track && <p>Трек: {activity.track.title}</p>}
                {activity.album && <p>Альбом: {activity.album.title}</p>}
                {activity.artist && (
                  <p>
                    Исполнитель:{" "}
                    {activity.artist.user?.username || activity.artist.email}
                  </p>
                )}
                <p>Время: {new Date(activity.timestamp).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Сообщение, если ничего не найдено */}
      {!searchResults.tracks.length &&
        !searchResults.artists.length &&
        !searchResults.albums.length &&
        !searchResults.playlists.length &&
        !searchResults.userActivities.length && (
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
