import React from "react";
import styles from "./Avatar.module.scss";
import { getFullImageUrl, getAvatarInitial } from "../../../utils/imageUtils";

/**
 * Компонент аватара с поддержкой изображения или заполнителя
 * @param {Object} props - Свойства компонента
 * @param {string} props.imageUrl - URL изображения аватара
 * @param {string} props.username - Имя пользователя для заполнителя
 * @param {string} props.size - Размер аватара ('sm', 'md', 'lg')
 * @param {string} props.className - Дополнительные CSS классы
 */
const Avatar = ({ imageUrl, username, size = "md", className = "" }) => {
  const sizeClass = styles[`avatar-${size}`] || styles["avatar-md"];

  return (
    <div className={`${styles.avatar} ${sizeClass} ${className}`}>
      {imageUrl ? (
        <img
          src={getFullImageUrl(imageUrl)}
          alt={`${username || "User"} avatar`}
          className={styles.avatarImage}
        />
      ) : (
        <div className={styles.avatarPlaceholder}>
          {getAvatarInitial(username)}
        </div>
      )}
    </div>
  );
};

export default Avatar;
