import { makeAutoObservable } from "mobx";
import axios from "../axios/axios";

class TrackStore {
  tracks = [];
  loading = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
  }

  fetchTracks = async () => {
    this.loading = true;
    try {
      const response = await axios.get("tracks/");
      this.tracks = response.data;
      this.error = null;
    } catch (error) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  };

  getTrack = async (id) => {
    this.loading = true;
    try {
      const response = await axios.get(`tracks/${id}/`);
      return response.data;
    } catch (error) {
      this.error = error.message;
      return null;
    } finally {
      this.loading = false;
    }
  };
}

export default new TrackStore();
