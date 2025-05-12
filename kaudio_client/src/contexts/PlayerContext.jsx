import { createContext, useState, useContext, useEffect } from "react";
import homeStore from "../stores/homeStore";

// Создаем контекст
const PlayerContext = createContext();

// Хук для использования контекста плеера
export const usePlayer = () => {
  return useContext(PlayerContext);
};

// Провайдер контекста плеера
export const PlayerProvider = ({ children }) => {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioSrc, setAudioSrc] = useState("");
  const [currentArtistId, setCurrentArtistId] = useState(null);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [playlist, setPlaylist] = useState([]);

  // Загрузка и воспроизведение трека
  const playTrack = async (track, tracks = [], index = 0) => {
    try {
      if (currentTrack?.id === track.id) {
        // Если тот же трек, просто переключаем play/pause
        setIsPlaying(!isPlaying);
        return;
      }

      // Получаем URL аудиофайла
      const audioUrl = await homeStore.getAudioFile(track.file);
      if (!audioUrl) {
        console.error("Не удалось получить URL аудиофайла");
        return;
      }

      // Обновляем состояние плеера
      setAudioSrc(audioUrl);
      setCurrentTrack(track);
      setIsPlaying(true);
      setCurrentArtistId(track.artist?.id || null);

      // Если предоставлен список треков, сохраняем его как текущий плейлист
      if (tracks && tracks.length > 0) {
        setPlaylist(tracks);
        setCurrentTrackIndex(index);
      }

      // Отправляем информацию о прослушивании
      try {
        await fetch(`http://localhost:8000/api/tracks/${track.id}/listen/`, {
          method: "POST",
          headers: {
            Authorization: `Token ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
          },
        });
      } catch (error) {
        console.error("Ошибка при отправке данных о прослушивании:", error);
      }
    } catch (error) {
      console.error("Ошибка при воспроизведении трека:", error);
    }
  };

  // Переключение на предыдущий трек
  const playPreviousTrack = () => {
    if (!playlist.length || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex > 0 ? currentTrackIndex - 1 : playlist.length - 1;

    playTrack(playlist[newIndex], playlist, newIndex);
  };

  // Переключение на следующий трек
  const playNextTrack = () => {
    if (!playlist.length || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex < playlist.length - 1 ? currentTrackIndex + 1 : 0;

    playTrack(playlist[newIndex], playlist, newIndex);
  };

  // Переключение play/pause
  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  // Значение контекста
  const value = {
    currentTrack,
    isPlaying,
    audioSrc,
    currentArtistId,
    playlist,
    currentTrackIndex,
    playTrack,
    playPreviousTrack,
    playNextTrack,
    togglePlay,
  };

  return (
    <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>
  );
};

export default PlayerContext;
