import React, { useState } from "react";
import TrackList from "../../components/TrackList/TrackList";
import AudioPlayer from "../../components/AudioPlayer/AudioPlayer";
import styles from "./MusicPage.module.scss";

const MusicPage = () => {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [tracks, setTracks] = useState([
    // Здесь будут загружаться треки с сервера
    {
      id: 1,
      title: "Пример трека",
      artist: "Исполнитель",
      album: "Альбом",
      duration: "3:45",
      url: "/path/to/track.mp3",
    },
  ]);

  const handleTrackSelect = (track) => {
    setCurrentTrack(track);
  };

  return (
    <div className={styles.musicPage}>
      <div className={styles.header}>
        <h1>Музыкальный каталог</h1>
        <div className={styles.filters}>{/* Здесь будут фильтры */}</div>
      </div>

      <div className={styles.content}>
        <TrackList tracks={tracks} onTrackSelect={handleTrackSelect} />
      </div>

      <AudioPlayer currentTrack={currentTrack} />
    </div>
  );
};

export default MusicPage;
