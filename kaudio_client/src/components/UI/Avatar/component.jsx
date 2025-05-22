import React from "react";
import styles from "./Avatar.module.scss";
import {
  getFullImageUrl,
  getAvatarInitial,
  getImageUrl,
} from "../../../utils/imageUtils";

/**
 * Компонент аватара с поддержкой изображения или заполнителя
 * @param {Object} props - Свойства компонента
 * @param {string} props.imageUrl - URL изображения аватара
 * @param {string} props.username - Имя пользователя для заполнителя
 * @param {string} props.size - Размер аватара ('sm', 'md', 'lg')
 * @param {string} props.className - Дополнительные CSS классы
 */
const Avatar = ({ imageUrl, username, size = "md", className = "" }) => {
  const finalImageUrl = getImageUrl(imageUrl);

  return (
    <div className={`${styles.avatar} ${styles[size]} ${className}`}>
      {finalImageUrl ? (
        <img
          src={getFullImageUrl(finalImageUrl)}
          alt={username}
          className={styles.avatarImage}
        />
      ) : (
        <span className={styles.avatarInitial}>
          {getAvatarInitial(username)}
        </span>
      )}
    </div>
  );
};

export default Avatar;
