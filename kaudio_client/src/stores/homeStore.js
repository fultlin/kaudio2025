import { makeAutoObservable, action } from "mobx";
import examplar from "axiosurl/axios";

class HomeStore {
  music = [];

  constructor() {
    makeAutoObservable(this, {
      setMusic: action,
      getTracks: action,
    });
  }

  setMusic(tracks) {
    this.music = tracks.traks || [];
  }

  async getTracks(track) {
    try {
      const response = await examplar.get(`music/${track}`);
      this.setMusic(response.data);
    } catch (error) {
      console.error("Ошибка при получении треков:", error);
      throw error;
    }
  }

  async loadAndPlayMusic(name) {
    try {
      const response = await fetch(
        `http://localhost:3000/music/stream/${name}`
      );
      if (!response.ok) {
        throw new Error("Failed to load music file");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      return url;
    } catch (error) {
      console.error("Error loading music file:", error);
      throw error;
    }
  }
}

const homeStore = new HomeStore();

export default homeStore;
