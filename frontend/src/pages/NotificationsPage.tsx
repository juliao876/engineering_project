import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar.tsx";
import Sidebar from "../components/Sidebar.tsx";
import { AuthAPI, NotificationsAPI } from "../services/api.ts";
import { useToast } from "../components/ToastProvider.tsx";
import useSidebarNavigation from "../hooks/useSidebarNavigation.ts";
import "../styles/NotificationsPage.css";
import "../styles/tokens.css";

interface NotificationItem {
  id: number;
  user_id: number;
  type: string;
  message: string;
  is_read: boolean;
  created_at?: string;
  read_at?: string | null;
  project_id?: number | null;
  actor_id?: number | null;
  actor_username?: string | null;
}

const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const sortedNotifications = useMemo(
    () =>
      [...notifications].sort((a, b) =>
        new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime(),
      ),
    [notifications],
  );

  const handleLogout = async () => {
    await AuthAPI.logout();
    localStorage.removeItem("token");
    navigate("/login");
  };

  const loadNotifications = async () => {
    setIsLoading(true);
    const response = await NotificationsAPI.getNotifications();
    if (response.ok) {
      const data = response.data || [];
      setNotifications(Array.isArray(data) ? data : []);
    } else {
      addToast({ message: "Unable to load notifications", type: "error" });
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleSidebarSelect = useSidebarNavigation();

  const markAsRead = async (notificationId: number) => {
    const response = await NotificationsAPI.markNotificationRead(notificationId);
    if (response.ok && response.data) {
      const updated = response.data as NotificationItem;
      setNotifications((prev) =>
        prev.map((notification) =>
          notification.id === notificationId
            ? { ...notification, ...updated }
            : notification,
        ),
      );
    }
  };

  const deleteNotification = async (notificationId: number) => {
    const response = await NotificationsAPI.deleteNotification(notificationId);
    if (response.ok) {
      setNotifications((prev) => prev.filter((notification) => notification.id !== notificationId));
    }
  };

  const handleNotificationClick = async (notification: NotificationItem) => {
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }

    if (notification.project_id) {
      navigate(`/analysis/${notification.project_id}`);
      return;
    }

    if (notification.type === "follow" && notification.actor_username) {
      navigate(`/users/${notification.actor_username}`);
    }
  };

  const formatDate = (value?: string) => {
    if (!value) return "";
    try {
      return new Date(value).toLocaleString();
    } catch (error) {
      return value;
    }
  };

  return (
    <div className="notifications-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        activeItem="notifications"
        onLogout={handleLogout}
        onSelect={handleSidebarSelect}
      />

      <Navbar onMenuClick={() => setIsSidebarOpen(true)} />

      <main className="notifications-page__main">
        <header className="notifications-page__header">
          <div>
            <p className="notifications-page__eyebrow">Stay updated</p>
            <h1 className="notifications-page__title">Notifications</h1>
            <p className="notifications-page__subtitle">
              You will be notified when someone follows you, rates your project, or responds to your comment.
            </p>
          </div>
        </header>

        <section className="notifications-page__list" aria-live="polite">
          {isLoading && <div className="notifications-page__loading">Loading notifications...</div>}

          {!isLoading && sortedNotifications.length === 0 && (
            <div className="notifications-page__empty">
              <p>No notifications yet.</p>
            </div>
          )}

          {sortedNotifications.map((notification) => (
            <article
              key={notification.id}
              className={`notifications-page__item ${notification.is_read ? "is-read" : ""}`}
              onClick={() => handleNotificationClick(notification)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  handleNotificationClick(notification);
                }
              }}
            >
              <div className="notifications-page__item-body">
                <div className="notifications-page__meta">
                  <span className={`notifications-page__badge notifications-page__badge--${notification.type}`}>
                    {notification.type}
                  </span>
                  <span className="notifications-page__time">{formatDate(notification.created_at)}</span>
                </div>
                <p className="notifications-page__message">{notification.message}</p>
              </div>

              <div className="notifications-page__actions">
                {!notification.is_read && (
                  <button
                    type="button"
                    className="notifications-page__action"
                    onClick={(event) => {
                      event.stopPropagation();
                      markAsRead(notification.id);
                    }}
                  >
                    Mark as read
                  </button>
                )}
                <button
                  type="button"
                  className="notifications-page__action notifications-page__action--danger"
                  onClick={(event) => {
                    event.stopPropagation();
                    deleteNotification(notification.id);
                  }}
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
};

export default NotificationsPage;