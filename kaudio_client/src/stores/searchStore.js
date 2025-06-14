import { makeAutoObservable } from "mobx";

class SearchStore {
  searchQuery = "";
  searchType = "tracks";
  filters = {
    genre: "",
    artist: "",
    album: "",
    release_date: "",
  };

  constructor() {
    makeAutoObservable(this);
  }

  setSearchQuery(query) {
    this.searchQuery = query;
  }

  setSearchType(type) {
    this.searchType = type;
  }

  setFilters(filters) {
    this.filters = filters;
  }

  resetFilters() {
    this.filters = {
      genre: "",
      artist: "",
      album: "",
      release_date: "",
    };
  }
}

export default new SearchStore();
