import { makeAutoObservable } from "mobx";
import instance from "../axios/axios";

class PlayerStore {
  trackUrl = "";
  trackId = null;
  trackName = "";
  author = "";
  isPlaying = false;
  currentTrackIndex = null;
  tracks = [];
  currentTrack = null;
  volume = 1;
  progress = 0;
  duration = 0;

  constructor() {
    makeAutoObservable(this);
  }

  // Установка данных трека
  setTrackData(trackId, trackName, author, trackUrl) {
    this.trackId = trackId;
    this.trackName = trackName;
    this.author = author;
    this.trackUrl = trackUrl;
  }

  // Загрузка и воспроизведение трека
  async loadTrack(track, index, tracksList = []) {
    try {
      if (this.trackId === track.id && this.isPlaying) {
        // Если тот же трек уже играет, ставим на паузу
        this.pause();
        return;
      }

      if (this.trackId === track.id && !this.isPlaying) {
        // Если тот же трек на паузе, продолжаем воспроизведение
        this.play();
        return;
      }

      // Загружаем новый трек
      const response = await instance.get(`tracks/${track.id}/stream/`, {
        responseType: "blob",
      });

      // Создаем URL для воспроизведения
      const audioUrl = URL.createObjectURL(response.data);

      // Обновляем данные для плеера
      this.setTrackData(
        track.id,
        track.title,
        track.artist
          ? track.artist.user?.username || track.artist.email
          : "Неизвестный исполнитель",
        audioUrl
      );

      this.currentTrackIndex = index;
      this.tracks = tracksList;
      this.play();

      // Увеличиваем счетчик прослушиваний
      await instance.post(`tracks/${track.id}/play/`);
    } catch (error) {
      console.error("Ошибка при воспроизведении трека:", error);
    }
  }

  // Воспроизведение
  play() {
    this.isPlaying = true;
  }

  // Пауза
  pause() {
    this.isPlaying = false;
  }

  // Следующий трек
  nextTrack() {
    if (!this.tracks.length || this.currentTrackIndex === null) return;

    const newIndex =
      this.currentTrackIndex < this.tracks.length - 1
        ? this.currentTrackIndex + 1
        : 0;

    this.loadTrack(this.tracks[newIndex], newIndex, this.tracks);
  }

  // Предыдущий трек
  prevTrack() {
    if (!this.tracks.length || this.currentTrackIndex === null) return;

    const newIndex =
      this.currentTrackIndex > 0
        ? this.currentTrackIndex - 1
        : this.tracks.length - 1;

    this.loadTrack(this.tracks[newIndex], newIndex, this.tracks);
  }

  setCurrentTrack = (track) => {
    this.currentTrack = track;
  };

  togglePlay = () => {
    this.isPlaying = !this.isPlaying;
  };

  setIsPlaying = (isPlaying) => {
    this.isPlaying = isPlaying;
  };

  setVolume = (volume) => {
    this.volume = Math.max(0, Math.min(1, volume));
  };

  setProgress = (progress) => {
    this.progress = progress;
  };

  setDuration = (duration) => {
    this.duration = duration;
  };

  resetPlayer = () => {
    this.currentTrack = null;
    this.isPlaying = false;
    this.progress = 0;
    this.duration = 0;
  };
}

export const playerStore = new PlayerStore();
export default playerStore;
