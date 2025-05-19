import React from "react";
import StatisticsComponent from "./components/Statistics";
import styles from "./Statistics.module.scss";

const StatisticsPage = () => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>Статистика платформы</h1>
        <p>Аналитика и статистические данные о музыкальном контенте</p>
      </div>
      <StatisticsComponent />
    </div>
  );
};

export default StatisticsPage;
