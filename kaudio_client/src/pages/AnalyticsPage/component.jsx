import { observer } from "mobx-react-lite";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import instance from "../../axios/axios";
import styles from "./AnalyticsPage.module.scss";
import authStore from "../../stores/authStore";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

const AnalyticsPage = observer(() => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [popularTracks, setPopularTracks] = useState([]);
  const [userActivity, setUserActivity] = useState([]);
  const [timeRange, setTimeRange] = useState("week"); // week, month, year

  useEffect(() => {
    if (!authStore.isAuthenticated || !authStore.isAdmin) {
      navigate("/");
      return;
    }

    // Проверяем наличие токена
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/auth");
      return;
    }

    // Устанавливаем токен для всех запросов
    instance.defaults.headers.common["Authorization"] = `Token ${token}`;

    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [tracksResponse, activityResponse] = await Promise.all([
        instance.get(`/tracks-analytics/?time_range=${timeRange}`),
        instance.get(`/user-activity/?time_range=${timeRange}`),
      ]);

      setPopularTracks(tracksResponse.data);
      setUserActivity(activityResponse.data);
      setError(null);
    } catch (err) {
      console.error("Ошибка при загрузке аналитики:", err);
      if (err.response?.status === 403) {
        setError(
          "У вас нет прав для просмотра аналитики. Пожалуйста, войдите как администратор."
        );
      } else {
        setError("Не удалось загрузить данные аналитики");
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
    });
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  return (
    <div className={styles.analyticsPage}>
      <h1>Аналитика</h1>

      <div className={styles.timeRangeSelector}>
        <button
          className={`${styles.timeButton} ${
            timeRange === "week" ? styles.active : ""
          }`}
          onClick={() => setTimeRange("week")}
        >
          Неделя
        </button>
        <button
          className={`${styles.timeButton} ${
            timeRange === "month" ? styles.active : ""
          }`}
          onClick={() => setTimeRange("month")}
        >
          Месяц
        </button>
        <button
          className={`${styles.timeButton} ${
            timeRange === "year" ? styles.active : ""
          }`}
          onClick={() => setTimeRange("year")}
        >
          Год
        </button>
      </div>

      <div className={styles.chartsContainer}>
        <div className={styles.chartSection}>
          <h2>Популярные треки</h2>
          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={popularTracks}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="title"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey="play_count"
                  name="Количество прослушиваний"
                  fill="#900066"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Активность пользователей</h2>
          <div className={styles.chart}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={userActivity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="active_users"
                  name="Активные пользователи"
                  stroke="#900066"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="new_users"
                  name="Новые пользователи"
                  stroke="#2ed573"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
});

export default AnalyticsPage;
