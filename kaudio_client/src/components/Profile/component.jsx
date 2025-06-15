import { observer } from "mobx-react-lite";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import instance from "../../axios/axios";
import authStore from "../../stores/authStore";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Clock, Music, Heart, UserPlus, Calendar, Filter } from "lucide-react";

import styles from "./Profile.module.scss";

const Profile = observer(() => {
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]);
  const [filteredActivities, setFilteredActivities] = useState([]);
  const [subscribes, setSubscribes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("history");
  const [activeFilter, setActiveFilter] = useState("all");

  const activityFilters = [
    { id: "all", label: "Все" },
    { id: "play", label: "Прослушивания" },
    { id: "like", label: "Лайки" },
    { id: "follow_artist", label: "Подписки" },
  ];

  useEffect(() => {
    if (!authStore.isAuthenticated) {
      navigate("/auth");
      return;
    }

    fetchUserData();
  }, []);

  useEffect(() => {
    if (activeFilter === "all") {
      setFilteredActivities(activities);
    } else {
      setFilteredActivities(
        activities.filter((activity) => activity.activity_type === activeFilter)
      );
    }
  }, [activeFilter, activities]);

  const fetchUserData = async () => {
    try {
      setIsLoading(true);
      const [activitiesRes, subscribesRes] = await Promise.all([
        instance.get(`users/${authStore.user.id}/activities/`),
        instance.get(`users/${authStore.user.id}/subscribes/`),
      ]);

      setActivities(activitiesRes.data);
      setFilteredActivities(activitiesRes.data);
      setSubscribes(subscribesRes.data);
    } catch (error) {
      console.error("Ошибка при загрузке данных:", error);
      setError("Не удалось загрузить данные");
    } finally {
      setIsLoading(false);
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case "play":
        return <Music size={20} />;
      case "like":
      case "like_album":
        return <Heart size={20} />;
      case "follow_artist":
        return <UserPlus size={20} />;
      default:
        return <Clock size={20} />;
    }
  };

  const getActivityText = (activity) => {
    switch (activity.activity_type) {
      case "play":
        return `Прослушан трек "${activity.track?.title}"`;
      case "like":
        return `Лайкнут трек "${activity.track?.title}"`;
      case "like_album":
        return `Лайкнут альбом "${activity.album?.title}"`;
      case "follow_artist":
        return `Подписка на исполнителя ${activity.artist?.user?.username}`;
      default:
        return "Неизвестное действие";
    }
  };

  const formatDate = (dateString) => {
    return format(new Date(dateString), "d MMMM yyyy, HH:mm", { locale: ru });
  };

  if (isLoading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  return (
    <div className={styles.profileContainer}>
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${
            activeTab === "history" ? styles.active : ""
          }`}
          onClick={() => setActiveTab("history")}
        >
          История прослушиваний
        </button>
        <button
          className={`${styles.tab} ${
            activeTab === "subscribes" ? styles.active : ""
          }`}
          onClick={() => setActiveTab("subscribes")}
        >
          Подписки
        </button>
      </div>

      {activeTab === "history" && (
        <div className={styles.historySection}>
          <div className={styles.historyHeader}>
            <h2>История активности</h2>
            <div className={styles.filters}>
              <Filter size={20} />
              {activityFilters.map((filter) => (
                <button
                  key={filter.id}
                  className={`${styles.filterButton} ${
                    activeFilter === filter.id ? styles.active : ""
                  }`}
                  onClick={() => setActiveFilter(filter.id)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
          {filteredActivities.length > 0 ? (
            <div className={styles.activitiesList}>
              {filteredActivities.map((activity) => (
                <div key={activity.id} className={styles.activityItem}>
                  <div className={styles.activityIcon}>
                    {getActivityIcon(activity.activity_type)}
                  </div>
                  <div className={styles.activityContent}>
                    <div className={styles.activityText}>
                      {getActivityText(activity)}
                    </div>
                    <div className={styles.activityTime}>
                      {formatDate(activity.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              {activeFilter === "all"
                ? "У вас пока нет истории активности"
                : "Нет активностей выбранного типа"}
            </div>
          )}
        </div>
      )}

      {activeTab === "subscribes" && (
        <div className={styles.subscribesSection}>
          <h2>Ваши подписки</h2>
          {subscribes.length > 0 ? (
            <div className={styles.subscribesList}>
              {subscribes.map((subscribe) => (
                <div key={subscribe.id} className={styles.subscribeItem}>
                  <div className={styles.subscribeInfo}>
                    <h3>{subscribe.subscribe.type}</h3>
                    <p>{subscribe.subscribe.permissions}</p>
                    <div className={styles.subscribeDates}>
                      <div>
                        <Calendar size={16} />
                        <span>Начало: {formatDate(subscribe.start_date)}</span>
                      </div>
                      {subscribe.end_date && (
                        <div>
                          <Calendar size={16} />
                          <span>
                            Окончание: {formatDate(subscribe.end_date)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              У вас пока нет активных подписок
            </div>
          )}
        </div>
      )}
    </div>
  );
});

export default Profile;
