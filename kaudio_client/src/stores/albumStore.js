import { makeAutoObservable } from "mobx";
import instance from "../axios/axios";

class AlbumStore {
  albums = [];
  currentAlbum = null;
  loading = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
  }

  fetchAlbums = async (artistId = null) => {
    this.loading = true;
    try {
      let url = "albums/";
      if (artistId) {
        url += `?artist_id=${artistId}`;
      }
      const response = await instance.get(url);
      this.albums = response.data;
      return response.data;
    } catch (error) {
      console.error("Ошибка при загрузке альбомов:", error);
      this.error = "Не удалось загрузить альбомы";
      return [];
    } finally {
      this.loading = false;
    }
  };

  fetchAlbumById = async (id) => {
    this.loading = true;
    try {
      const response = await instance.get(`albums/${id}/`);
      this.currentAlbum = response.data;
      return response.data;
    } catch (error) {
      console.error(`Ошибка при загрузке альбома с ID ${id}:`, error);
      this.error = "Не удалось загрузить альбом";
      return null;
    } finally {
      this.loading = false;
    }
  };

  createAlbum = async (albumData) => {
    this.loading = true;
    try {
      const response = await instance.post("albums/", albumData);
      this.albums = [...this.albums, response.data];
      return response.data;
    } catch (error) {
      console.error("Ошибка при создании альбома:", error);
      this.error = error.response?.data?.error || "Не удалось создать альбом";
      throw error;
    } finally {
      this.loading = false;
    }
  };
}

export default new AlbumStore();
