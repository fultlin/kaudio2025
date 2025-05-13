import { useState } from "react";
import Album from "./component";
import MiniPlayer from "../MiniPlayer/component";
import styles from "./Album.module.scss";
import { Link, useNavigate } from "react-router-dom";
import authStore from "../../stores/authStore";
import UploadIcon from "../Home/components/UploadIcon";

const AlbumWithPlayer = () => {
  const navigate = useNavigate();
  const [trackName, setTrackName] = useState("");
  const [author, setAuthor] = useState("");
  const [src, setSrc] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTrackId, setActiveTrackId] = useState(null);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [tracks, setTracks] = useState([]);

  const user = authStore.user;
  const isArtist = authStore.isArtist;

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handlePrevTrack = () => {
    if (tracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex > 0 ? currentTrackIndex - 1 : tracks.length - 1;

    // Эмулируем клик на предыдущий трек
    if (tracks[newIndex]) {
      // Обновляем необходимые данные
      setCurrentTrackIndex(newIndex);
    }
  };

  const handleNextTrack = () => {
    if (tracks.length === 0 || currentTrackIndex === null) return;

    const newIndex =
      currentTrackIndex < tracks.length - 1 ? currentTrackIndex + 1 : 0;

    // Эмулируем клик на следующий трек
    if (tracks[newIndex]) {
      // Обновляем необходимые данные
      setCurrentTrackIndex(newIndex);
    }
  };

  // Обработчик клика по профилю пользователя
  const handleProfileClick = () => {
    navigate("/settings");
  };

  return (
    <div className={styles.mainContainer}>
      <div className={styles.appContent}>

        <div className={styles.contentArea}>
          <Album
            setTrackName={setTrackName}
            setAuthor={setAuthor}
            setSrc={setSrc}
            setIsPlaying={setIsPlaying}
            setActiveTrackId={setActiveTrackId}
            setCurrentTrackIndex={setCurrentTrackIndex}
            setTracks={setTracks}
            activeTrackId={activeTrackId}
            isPlaying={isPlaying}
            currentTrackIndex={currentTrackIndex}
            tracks={tracks}
          />
        </div>
      </div>
      <div className={styles.playerContainer}>
        <MiniPlayer
          trackName={trackName}
          author={author}
          name={src}
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
          onPrev={handlePrevTrack}
          onNext={handleNextTrack}
        />
      </div>
    </div>
  );
};

export default AlbumWithPlayer;
