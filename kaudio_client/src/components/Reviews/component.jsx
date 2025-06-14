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

  const { user } = authStore;

  useEffect(() => {
    fetchReviews();
  }, [type, id]);

  const fetchReviews = async () => {
    try {
      const response = await instance.get(
        `${type.replace("s", "")}-reviews/?${type.replace("s", "")}_id=${id}`
      );
      if (response.status === 200) {
        setReviews(response.data);
      }
    } catch (error) {
      console.error("Ошибка при загрузке отзывов:", error);
      setError("Не удалось загрузить отзывы");
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
          text: reviewText,
          [type.replace("s", "")]: id,
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
      setError("Не удалось отправить отзыв");
    } finally {
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
        {user && (
          <button
            className={styles.addReviewButton}
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? "Отмена" : "Добавить отзыв"}
          </button>
        )}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {showForm && (
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
              <span className={styles.reviewAuthor}>{review.author}</span>
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
