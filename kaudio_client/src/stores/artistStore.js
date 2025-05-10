import { makeAutoObservable } from "mobx";
import axios from "../axios/axios";

class ArtistStore {
  artists = [];
  loading = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
  }

  fetchArtists = async () => {
    this.loading = true;
    try {
      const response = await axios.get("artists/");
      this.artists = response.data;
      this.error = null;
    } catch (error) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  };

  getArtist = async (id) => {
    this.loading = true;
    try {
      const response = await axios.get(`artists/${id}/`);
      return response.data;
    } catch (error) {
      this.error = error.message;
      return null;
    } finally {
      this.loading = false;
    }
  };
}

export default new ArtistStore();
