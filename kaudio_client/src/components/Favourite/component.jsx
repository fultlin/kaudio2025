import styles from "./Player.module.scss";
import music from "../../assets/sayhello.mp3";


export default function Music() {

    const play = () => {
        const player = document.getElementById('player')

        player.play()
    }

  return (
    <>
      <audio id="player" className={styles.player} src={music} controls>
        <source src={music} />
      </audio>

      <button onClick={() => {play()}}>Play</button>
    </>
  );
}
