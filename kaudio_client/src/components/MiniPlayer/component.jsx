import { useEffect, useRef, useState } from "react";
import styles from "./MiniPlayer.module.scss";

export default function MiniPlayer({
  name,
  isPlaying,
  onPlayPause,
  onPrev,
  onNext,
  trackName,
  author,
}) {
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const playerRef = useRef(null);

  // Загружаем трек и сбрасываем состояние
  useEffect(() => {
    if (name) {
      const audioElement = playerRef.current;

      audioElement.pause();
      audioElement.src = name;
      audioElement.load();

      // Обновляем продолжительность трека после загрузки метаданных
      audioElement.onloadedmetadata = () => {
        setDuration(audioElement.duration);
      };
    }
  }, [name]);

  // Управляем воспроизведением/паузой
  useEffect(() => {
    const audioElement = playerRef.current;
    if (isPlaying && name) {
      audioElement.play().catch((error) => {
        console.error("Ошибка воспроизведения:", error);
      });
    } else {
      audioElement.pause();
    }
  }, [isPlaying, name]);

  // Обновляем текущее время трека
  useEffect(() => {
    const audioElement = playerRef.current;

    const updateCurrentTime = () => {
      setCurrentTime(audioElement.currentTime);
    };

    // Слушаем событие обновления времени
    audioElement.addEventListener("timeupdate", updateCurrentTime);

    return () => {
      // Очищаем обработчик событий при размонтировании
      audioElement.removeEventListener("timeupdate", updateCurrentTime);
    };
  }, []);

  // Обработчик перемотки трека вручную
  const handleTimeChange = (event) => {
    const audioElement = playerRef.current;
    audioElement.currentTime = event.target.value;
    setCurrentTime(audioElement.currentTime);
  };

  // Управляем изменением громкости
  const handleVolumeChange = (event) => {
    const audioElement = playerRef.current;
    audioElement.volume = event.target.value;
    setVolume(audioElement.volume);
  };

  // Перемотка вперед
  const skipForward = () => {
    const audioElement = playerRef.current;
    audioElement.currentTime += 10;
  };

  // Перемотка назад
  const skipBackward = () => {
    const audioElement = playerRef.current;
    audioElement.currentTime -= 10;
  };

  return (
    <div className={styles.player}>
      <audio id="mini-player" ref={playerRef}></audio>
      <div className={styles.trackinfo}>
        <p>{trackName || "....."}</p>
        <p>{author || "....."}</p>
      </div>

      <div className={styles.controls}>
        <div className={styles.controlButtons}>
          <button onClick={onPrev}>Previous</button>
          <button onClick={onPlayPause}>{isPlaying ? "Pause" : "Play"}</button>
          <button onClick={onNext}>Next</button>
          <button onClick={skipBackward}>-10</button>
          <button onClick={skipForward}>+10</button>
        </div>

        <div className={styles.timeControls}>
          <span>
            {Math.floor(currentTime / 60)}:
            {Math.floor(currentTime % 60)
              .toString()
              .padStart(2, "0")}
          </span>
          <input
            type="range"
            min="0"
            max={duration}
            value={currentTime}
            onChange={handleTimeChange}
          />
          <span>
            {Math.floor(duration / 60)}:
            {Math.floor(duration % 60)
              .toString()
              .padStart(2, "0")}
          </span>
        </div>
      </div>

      <div className={styles.volumeControls}>
        <svg
          width="32"
          height="30"
          viewBox="0 0 32 30"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M22.5734 5.12522C22.3569 5.0374 22.1194 5.00501 21.8851 5.03137C21.6509 5.05772 21.4283 5.14187 21.2401 5.27522L14.8667 10.0002H10.0001C9.64646 10.0002 9.30732 10.1319 9.05727 10.3663C8.80722 10.6008 8.66675 10.9187 8.66675 11.2502V18.7502C8.66675 19.0817 8.80722 19.3997 9.05727 19.6341C9.30732 19.8685 9.64646 20.0002 10.0001 20.0002H14.8667L21.1734 24.7252C21.408 24.9017 21.6993 24.9986 22.0001 25.0002C22.1992 25.0033 22.3961 24.9604 22.5734 24.8752C22.8003 24.7739 22.992 24.6145 23.1265 24.4155C23.261 24.2165 23.3327 23.9858 23.3334 23.7502V6.25022C23.3327 6.01462 23.261 5.78399 23.1265 5.58495C22.992 5.3859 22.8003 5.22653 22.5734 5.12522ZM20.6667 21.1502L16.1601 17.7752C15.9255 17.5988 15.6342 17.5019 15.3334 17.5002H11.3334V12.5002H15.3334C15.6342 12.4986 15.9255 12.4017 16.1601 12.2252L20.6667 8.85022V21.1502Z"
            fill="#f7f7f7"
          />
        </svg>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={volume}
          onChange={handleVolumeChange}
        />
      </div>
    </div>
  );
}
