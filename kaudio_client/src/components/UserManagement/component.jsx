import { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import axios from "../../axios/axios";
import styles from "./styles.module.scss";
import authStore from "../../stores/authStore";
import { useNavigate } from "react-router-dom";

const UserManagement = observer(() => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingRole, setEditingRole] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Проверяем, является ли пользователь администратором
    if (!authStore.isAdmin) {
      navigate("/");
      return;
    }

    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get("/users/");
      setUsers(response.data);
      setLoading(false);
    } catch (err) {
      setError("Ошибка при загрузке пользователей");
      setLoading(false);
    }
  };

  const handleBlockUser = async (userId) => {
    try {
      await axios.post(`/users/${userId}/block/`);
      fetchUsers(); // Обновляем список после блокировки
    } catch (err) {
      setError("Ошибка при блокировке пользователя");
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm("Вы уверены, что хотите удалить этого пользователя?")) {
      try {
        await axios.delete(`/users/${userId}/`);
        fetchUsers(); // Обновляем список после удаления
      } catch (err) {
        setError("Ошибка при удалении пользователя");
      }
    }
  };

  const handleChangeRole = async (userId, newRole) => {
    try {
      await axios.patch(`/users/${userId}/`, { role: newRole });
      setEditingRole(null); // Закрываем режим редактирования
      fetchUsers(); // Обновляем список после изменения роли
    } catch (err) {
      setError("Ошибка при изменении роли пользователя");
    }
  };

  const startEditingRole = (userId) => {
    setEditingRole(userId);
  };

  const cancelEditingRole = () => {
    setEditingRole(null);
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  return (
    <div className={styles.container}>
      <h1>Управление пользователями</h1>
      <div className={styles.userList}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Имя пользователя</th>
              <th>Email</th>
              <th>Роль</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  {editingRole === user.id ? (
                    <div className={styles.roleEdit}>
                      <select
                        defaultValue={user.role}
                        onChange={(e) =>
                          handleChangeRole(user.id, e.target.value)
                        }
                        className={styles.roleSelect}
                      >
                        <option value="user">Пользователь</option>
                        <option value="admin">Администратор</option>
                      </select>
                      <button
                        onClick={cancelEditingRole}
                        className={styles.cancelButton}
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <div
                      className={`${styles.role} ${styles[user.role]}`}
                      onClick={() => startEditingRole(user.id)}
                    >
                      {user.role === "admin" && "Администратор"}
                      {user.role === "artist" && "Артист"}
                      {user.role === "user" && "Пользователь"}
                      <span className={styles.editIcon}>✎</span>
                    </div>
                  )}
                </td>
                <td>
                  <div
                    className={`${styles.status} ${
                      user.is_blocked ? styles.blocked : styles.active
                    }`}
                  >
                    {user.is_blocked ? "Заблокирован" : "Активен"}
                  </div>
                </td>
                <td>
                  <button
                    onClick={() => handleBlockUser(user.id)}
                    className={styles.blockButton}
                  >
                    {user.is_blocked ? "Разблокировать" : "Заблокировать"}
                  </button>
                  <button
                    onClick={() => handleDeleteUser(user.id)}
                    className={styles.deleteButton}
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});

export default UserManagement;
