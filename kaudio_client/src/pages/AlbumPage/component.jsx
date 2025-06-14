import Reviews from "../../components/Reviews/component";

const AlbumPage = observer(() => {
  return (
    <div className={styles.albumPage}>
      <div className={styles.albumInfo}>{/* ... existing code ... */}</div>

      <Reviews type="albums" id={id} />
    </div>
  );
});

export default AlbumPage;
