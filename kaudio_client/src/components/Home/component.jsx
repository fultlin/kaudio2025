import { observer } from "mobx-react-lite";
import MiniPlayer from "../MiniPlayer/component";
import { Link } from "react-router-dom";
import Search from "../Search/component";
import homeStore from "stores/homeStore";
import { toJS } from "mobx";
import { useEffect, useState } from "react";

import styles from "./Home.module.scss";
import UploadIcon from "./components/UploadIcon";

const Home = observer(() => {
  const [allTracks, setAllTracks] = useState([]);
  const [src, setSrc] = useState("");
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const tracks = toJS(homeStore.music) || [];
  const [trackName, setTrackName] = useState("");
  const [author, setAuthor] = useState("");

  useEffect(() => {
    if (
      Array.isArray(tracks) &&
      JSON.stringify(tracks) !== JSON.stringify(allTracks)
    ) {
      setAllTracks(tracks);
      console.log(tracks);
    }
  }, [tracks]);

  // Загрузка трека и автоматическое воспроизведение
  const loadAndPlayTrack = async (index) => {
    const track = allTracks[index];
    if (track) {
      const url = await homeStore.loadAndPlayMusic(track.name);
      setTrackName(track.name.slice(0, -4));
      setAuthor(track.author);
      setSrc(url);
      setIsPlaying(true); // Автоматическое воспроизведение
    }
  };

  const handleTrackClick = (index) => {
    setCurrentTrackIndex(index);
    loadAndPlayTrack(index); // Загружаем и автоматически воспроизводим трек
  };

  const handlePrevTrack = () => {
    const newIndex =
      currentTrackIndex > 0 ? currentTrackIndex - 1 : allTracks.length - 1;
    setCurrentTrackIndex(newIndex);
    loadAndPlayTrack(newIndex);
  };

  const handleNextTrack = () => {
    const newIndex =
      currentTrackIndex < allTracks.length - 1 ? currentTrackIndex + 1 : 0;
    setCurrentTrackIndex(newIndex);
    loadAndPlayTrack(newIndex);
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying); // Переключение между воспроизведением и паузой
  };

  return (
    <>
      <aside className={styles.aside}>цййцйц</aside>
      <div className={styles.content}>
        <div className={styles.upper__home}>
          <Link to="upload">
            <UploadIcon />
          </Link>
        </div>
        <ul className={styles.track__list}>
          {Array.isArray(allTracks) && allTracks.length > 0 ? (
            allTracks.map((track, index) => (
              <li
                key={track.id}
                onClick={() => handleTrackClick(index)} // Клик на трек
                className={styles.track}
              >
                <div>{index + 1}</div>
                <div>
                  <span className={styles.track__information__name}>
                    {track.name.slice(0, -4)}
                  </span>
                  <span className={styles.track__information__author}>
                    {track.author}
                  </span>
                </div>
              </li>
            ))
          ) : (
            <div>No tracks available</div>
          )}
        </ul>
      </div>

      <MiniPlayer
        trackName={trackName}
        author={author}
        name={src}
        isPlaying={isPlaying}
        onPlayPause={handlePlayPause}
        onPrev={handlePrevTrack}
        onNext={handleNextTrack}
      />
    </>
  );
});

export default Home;
