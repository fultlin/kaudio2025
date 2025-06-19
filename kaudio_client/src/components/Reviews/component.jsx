import React, { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import { Star } from "lucide-react";
import styles from "./Reviews.module.scss";
import instance from "../../axios/axios";
import authStore from "../../stores/authStore";

const Reviews = observer(({ type, id }) => {
  const [reviews, setReviews] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [rating, setRating] = useState(0);
  const [reviewText, setReviewText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [canReview, setCanReview] = useState(false);

  const { user } = authStore;

  useEffect(() => {
    fetchReviews();
    checkCanReview();
  }, [type, id, user]);

  const fetchReviews = async () => {
    try {
      let response;
      if (type === "tracks") {
        response = await instance.get("/optimized/reviews/");
        if (response.status === 200 && response.data && response.data.data) {
          setReviews(response.data.data);
        }
      } else if (type === "playlists") {
        response = await instance.get("/optimized/playlists/");
        if (response.status === 200 && response.data && response.data.data) {
          const allReviews = response.data.data.flatMap(
            (pl) => pl.reviews || []
          );
          setReviews(allReviews);
        }
      } else {
        response = await instance.get(
          `${type.replace("s", "")}-reviews/?${type.replace("s", "")}_id=${id}`
        );
        if (response.status === 200) {
          setReviews(response.data);
        }
      }
    } catch (error) {
      console.error("Ошибка при загрузке отзывов:", error);
      setError("Не удалось загрузить отзывы");
    }
  };

  const checkCanReview = async () => {
    if (!user) {
      setCanReview(false);
      return;
    }
    try {
      let url = "";
      if (type === "tracks") {
        url = `/user-activities/?user_id=${user.id}&activity_type=play&track_id=${id}`;
      } else if (type === "albums") {
        url = `/user-activities/?user_id=${user.id}&activity_type=play&album_id=${id}`;
      }
      const response = await instance.get(url);
      if (type === "tracks") {
        setCanReview(
          Array.isArray(response.data) &&
            response.data.some(
              (activity) => activity.track && activity.track.id == id
            )
        );
      } else if (type === "albums") {
        setCanReview(
          Array.isArray(response.data) &&
            response.data.some(
              (activity) => activity.album && activity.album.id == id
            )
        );
      }
    } catch (e) {
      setCanReview(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setError("Необходимо войти в систему");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await instance.post(
        `${type.replace("s", "")}-reviews/`,
        {
          rating,
          [type.replace("s", "")]: id,
          text: reviewText,
        }
      );

      if (response.status === 201) {
        setReviews([...reviews, response.data]);
        setRating(0);
        setReviewText("");
        setShowForm(false);
      }
    } catch (error) {
      console.error("Ошибка при отправке отзыва:", error);
      if (error.response?.data?.non_field_errors) {
        setError(error.response.data.non_field_errors.join(" "));
      } else if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError("Не удалось отправить отзыв");
      }
      setLoading(false);
    }
  };

  const handleDelete = async (reviewId) => {
    try {
      const response = await instance.delete(
        `${type.replace("s", "")}-reviews/${reviewId}/`
      );
      if (response.status === 204) {
        setReviews(reviews.filter((review) => review.id !== reviewId));
      }
    } catch (error) {
      console.error("Ошибка при удалении отзыва:", error);
      setError("Не удалось удалить отзыв");
    }
  };

  const renderStars = (value, interactive = false) => {
    return [...Array(5)].map((_, index) => (
      <Star
        key={index}
        className={`${styles.star} ${index < value ? styles.active : ""}`}
        size={20}
        onClick={() => interactive && setRating(index + 1)}
      />
    ));
  };

  return (
    <div className={styles.reviewsContainer}>
      <div className={styles.reviewsHeader}>
        <h3 className={styles.reviewsTitle}>Отзывы</h3>
        {user && canReview && (
          <button
            className={styles.addReviewButton}
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? "Отмена" : "Добавить отзыв"}
          </button>
        )}
      </div>

      {user && !canReview && (
        <div className={styles.error}>
          Вы не можете оставить отзыв на{" "}
          {type === "tracks"
            ? "трек"
            : type === "playlists"
            ? "плейлист"
            : "альбом"}
          , который не прослушивали.
        </div>
      )}

      {error && <div className={styles.error}>{error}</div>}

      {showForm && canReview && (
        <form className={styles.reviewForm} onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <div className={styles.ratingGroup}>
              <span className={styles.ratingLabel}>Оценка:</span>
              <div className={styles.ratingStars}>
                {renderStars(rating, true)}
              </div>
            </div>
          </div>

          <div className={styles.formGroup}>
            <textarea
              className={styles.reviewText}
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              placeholder="Напишите ваш отзыв..."
              required
            />
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={loading || !rating || !reviewText}
          >
            {loading ? "Отправка..." : "Отправить отзыв"}
          </button>
        </form>
      )}

      <div className={styles.reviewsList}>
        {reviews.map((review) => (
          <div key={review.id} className={styles.reviewItem}>
            <div className={styles.reviewHeader}>
              <span className={styles.reviewAuthor}>
                {review.author?.username || review.author?.email || "Аноним"}
              </span>
              <span className={styles.reviewDate}>
                {new Date(review.created_at).toLocaleDateString()}
              </span>
            </div>

            <div className={styles.reviewRating}>
              {renderStars(review.rating)}
            </div>

            <p className={styles.reviewContent}>{review.text}</p>

            {user && (user.id === review.author_id || user.is_staff) && (
              <div className={styles.reviewActions}>
                <button
                  className={styles.actionButton}
                  onClick={() => handleDelete(review.id)}
                >
                  Удалить
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
});

export default Reviews;
