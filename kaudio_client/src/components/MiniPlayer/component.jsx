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

      <div className={styles.trackInfo}>
        {trackName ? (
          <>
            <div className={styles.trackName}>{trackName}</div>
            <div className={styles.trackAuthor}>{author}</div>
          </>
        ) : (
          <div className={styles.noTrack}>
            Выберите трек для воспроизведения
          </div>
        )}
      </div>

      <div className={styles.controlsWrapper}>
        <div className={styles.mainControls}>
          <button
            className={styles.controlBtn}
            onClick={onPrev}
            title="Предыдущий"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M19 5L9 12L19 19V5Z" fill="currentColor" />
              <path d="M7 5H5V19H7V5Z" fill="currentColor" />
            </svg>
          </button>

          <button
            className={`${styles.controlBtn} ${styles.playBtn}`}
            onClick={onPlayPause}
            title={isPlaying ? "Пауза" : "Воспроизвести"}
          >
            {isPlaying ? (
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M10 4H6V20H10V4Z" fill="currentColor" />
                <path d="M18 4H14V20H18V4Z" fill="currentColor" />
              </svg>
            ) : (
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M6 4L20 12L6 20V4Z" fill="currentColor" />
              </svg>
            )}
          </button>

          <button
            className={styles.controlBtn}
            onClick={onNext}
            title="Следующий"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M5 5L15 12L5 19V5Z" fill="currentColor" />
              <path d="M17 5H19V19H17V5Z" fill="currentColor" />
            </svg>
          </button>
        </div>

        <div className={styles.timeControls}>
          <span className={styles.timeDisplay}>
            {Math.floor(currentTime / 60)}:
            {Math.floor(currentTime % 60)
              .toString()
              .padStart(2, "0")}
          </span>

          <div className={styles.progressBar}>
            <input
              type="range"
              min="0"
              max={duration || 0}
              value={currentTime}
              onChange={handleTimeChange}
              className={styles.progressInput}
            />
          </div>

          <span className={styles.timeDisplay}>
            {Math.floor(duration / 60)}:
            {Math.floor(duration % 60)
              .toString()
              .padStart(2, "0")}
          </span>
        </div>
      </div>

      <div className={styles.volumeControls}>
        <button
          className={styles.controlBtn}
          onClick={() =>
            handleVolumeChange({ target: { value: volume === 0 ? 0.5 : 0 } })
          }
          title={volume === 0 ? "Включить звук" : "Выключить звук"}
        >
          {volume === 0 ? (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M3 9H7L12 4V20L7 15H3V9Z" fill="currentColor" />
              <path
                d="M16.5 12L21 16.5M16.5 16.5L21 12"
                stroke="currentColor"
                strokeWidth="2"
              />
            </svg>
          ) : (
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M3 9H7L12 4V20L7 15H3V9Z" fill="currentColor" />
              <path
                d="M16 9C16 9 18 10.5 18 12C18 13.5 16 15 16 15"
                stroke="currentColor"
                strokeWidth="2"
              />
              <path
                d="M19 7C19 7 22 9 22 12C22 15 19 17 19 17"
                stroke="currentColor"
                strokeWidth="2"
              />
            </svg>
          )}
        </button>

        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={volume}
          onChange={handleVolumeChange}
          className={styles.volumeInput}
        />
      </div>
    </div>
  );
}
