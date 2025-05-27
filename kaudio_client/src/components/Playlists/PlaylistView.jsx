import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import instance from "../../axios/axios";
import MiniPlayer from "../MiniPlayer/component";
import styles from "./PlaylistView.module.scss";
import playerStore from "../../stores/playerStore";
import { observer } from "mobx-react-lite";

const PlaylistView = observer(() => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [playlist, setPlaylist] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showAddTrackModal, setShowAddTrackModal] = useState(false);

  useEffect(() => {
    fetchPlaylistData();
  }, [id]);

  const fetchPlaylistData = async () => {
    try {
      setLoading(true);
      const response = await instance.get(`/playlists/${id}/`);
      setPlaylist(response.data);
      setTracks(response.data.tracks || []);
      setError(null);
    } catch (err) {
      setError("Ошибка при загрузке плейлиста");
      console.error("Ошибка:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayTrack = async (track, index) => {
    try {
      if (playerStore.trackId === track.id) {
        // Если тот же трек уже играет, переключаем воспроизведение/паузу
        if (playerStore.isPlaying) {
          playerStore.pause();
        } else {
          playerStore.play();
        }
        return;
      }

      console.log("Загрузка трека:", track.title);

      // Загружаем аудиофайл трека
      const response = await instance.get(`tracks/${track.id}/stream/`, {
        responseType: "blob",
      });

      console.log("Получен ответ от сервера:", response.status);

      // Создаем URL для воспроизведения
      const audioUrl = URL.createObjectURL(response.data);
      console.log("Создан URL для воспроизведения:", audioUrl);

      // Загружаем трек в плеер
      playerStore.loadTrack(
        {
          ...track,
          file_url: audioUrl,
        },
        index,
        tracks
      );

      console.log("Трек загружен в плеер:", {
        id: playerStore.trackId,
        name: playerStore.trackName,
        url: playerStore.trackUrl,
      });

      // Увеличиваем счетчик прослушиваний
      await instance.post(`tracks/${track.id}/play/`);
    } catch (err) {
      console.error("Ошибка при воспроизведении трека:", err);
      setError("Ошибка при воспроизведении трека");
    }
  };

  const handleSearchTracks = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await instance.get(`tracks/`, {
        params: {
          search: searchQuery,
        },
      });

      // Фильтруем треки, которые уже есть в плейлисте
      const existingTrackIds = tracks.map((track) => track.id);
      const filteredResults = response.data.filter(
        (track) => !existingTrackIds.includes(track.id)
      );

      setSearchResults(filteredResults);
    } catch (err) {
      console.error("Ошибка при поиске треков:", err);
      setError("Ошибка при поиске треков");
    }
  };

  const handleAddTrack = async (trackId) => {
    try {
      // Проверяем, есть ли уже такой трек в плейлисте
      const existingTracks = await instance.get(`playlist-tracks/`, {
        params: {
          playlist_id: id,
          track_id: trackId,
        },
      });

      if (existingTracks.data && existingTracks.data.length > 0) {
        setError("Этот трек уже есть в плейлисте");
        return;
      }

      // Если трека нет, добавляем его
      await instance.post(`playlist-tracks/`, {
        playlist_id: id,
        track_id: trackId,
        position: tracks.length + 1,
      });

      fetchPlaylistData(); // Обновляем список треков
      setShowAddTrackModal(false);
      setSearchQuery("");
      setSearchResults([]);
    } catch (err) {
      console.error("Ошибка при добавлении трека:", err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 500) {
        setError(
          "Ошибка сервера при добавлении трека. Возможно, трек уже есть в плейлисте."
        );
      } else {
        setError("Ошибка при добавлении трека");
      }
    }
  };

  const handleRemoveTrack = async (trackId) => {
    if (
      window.confirm("Вы уверены, что хотите удалить этот трек из плейлиста?")
    ) {
      try {
        // Находим ID записи PlaylistTrack
        const playlistTrack = await instance.get(`playlist-tracks/`, {
          params: {
            playlist_id: id,
            track_id: trackId,
          },
        });

        if (playlistTrack.data && playlistTrack.data.length > 0) {
          await instance.delete(`playlist-tracks/${playlistTrack.data[0].id}/`);
          fetchPlaylistData();
        } else {
          throw new Error("Трек не найден в плейлисте");
        }
      } catch (err) {
        console.error("Ошибка при удалении трека:", err);
        if (err.response?.data?.detail) {
          setError(err.response.data.detail);
        } else {
          setError("Ошибка при удалении трека");
        }
      }
    }
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  return (
    <div className={styles.playlistView}>
      <div className={styles.playlistHeader}>
        <div className={styles.playlistInfo}>
          <div className={styles.coverImage}>
            {playlist?.cover_image ? (
              <img src={playlist.cover_image} alt={playlist.title} />
            ) : (
              <div className={styles.defaultCover}>🎵</div>
            )}
          </div>
          <div className={styles.details}>
            <h1>{playlist?.title}</h1>
            <p className={styles.description}>
              {playlist?.description || "Нет описания"}
            </p>
            <p className={styles.trackCount}>Треков: {tracks.length}</p>
          </div>
        </div>
        <div className={styles.actions}>
          <button
            onClick={() => navigate(`/playlists/${id}/edit`)}
            className={styles.editButton}
          >
            Редактировать
          </button>
          <button
            onClick={() => setShowAddTrackModal(true)}
            className={styles.addButton}
          >
            Добавить треки
          </button>
        </div>
      </div>

      <div className={styles.tracksList}>
        {tracks.map((track, index) => (
          <div key={track.id} className={styles.trackItem}>
            <div
              className={styles.trackInfo}
              onClick={() => handlePlayTrack(track, index)}
            >
              <span className={styles.trackNumber}>{index + 1}</span>
              <div className={styles.trackDetails}>
                <span className={styles.trackTitle}>{track.title}</span>
                <span className={styles.trackArtist}>
                  {track.artist?.email || "Неизвестный исполнитель"}
                </span>
              </div>
              <span className={styles.playStatus}>
                {playerStore.trackId === track.id
                  ? playerStore.isPlaying
                    ? "⏸"
                    : "▶"
                  : "▶"}
              </span>
            </div>
            <button
              onClick={() => handleRemoveTrack(track.id)}
              className={styles.removeButton}
            >
              Удалить
            </button>
          </div>
        ))}
      </div>

      {showAddTrackModal && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2>Добавить треки</h2>
            <div className={styles.searchBox}>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Поиск треков..."
              />
              <button onClick={handleSearchTracks}>Поиск</button>
            </div>
            <div className={styles.searchResults}>
              {searchResults.map((track) => (
                <div key={track.id} className={styles.searchResultItem}>
                  <div className={styles.trackInfo}>
                    <span className={styles.trackTitle}>{track.title}</span>
                    <span className={styles.trackArtist}>
                      {track.artist?.email || "Неизвестный исполнитель"}
                    </span>
                  </div>
                  <button onClick={() => handleAddTrack(track.id)}>
                    Добавить
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowAddTrackModal(false)}
              className={styles.closeButton}
            >
              Закрыть
            </button>
          </div>
        </div>
      )}

      <div className={styles.playerContainer}>
        <MiniPlayer
          trackName={playerStore.trackName}
          author={playerStore.author}
          isPlaying={playerStore.isPlaying}
          name={playerStore.trackUrl}
          onPlayPause={() =>
            playerStore.isPlaying ? playerStore.pause() : playerStore.play()
          }
          onPrev={() => playerStore.prevTrack()}
          onNext={() => playerStore.nextTrack()}
        />
      </div>
    </div>
  );
});

export default PlaylistView;
