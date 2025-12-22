import React, { useCallback, useEffect, useState } from "react";
import "../styles/Toast.css";

export type ToastType = "success" | "error";

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onClose?: () => void;
}

const Toast: React.FC<ToastProps> = ({
  message,
  type = "success",
  duration = 4000,
  onClose,
}) => {
  const [isClosing, setIsClosing] = useState(false);

  const exitAnimationDuration = 520;

  const closeToast = useCallback(() => {
    if (isClosing) return;
    setIsClosing(true);
    setTimeout(() => {
      onClose?.();
    }, exitAnimationDuration);
  }, [exitAnimationDuration, isClosing, onClose]);

  useEffect(() => {
    if (!duration) return;
    const closeTimer = setTimeout(closeToast, duration);

    return () => {
      clearTimeout(closeTimer);
    };
  }, [closeToast, duration]);

  const progressStyle: React.CSSProperties & { ["--toast-duration"]?: string } = {
    "--toast-duration": `${duration}ms`,
  };

  return (
    <div
      className={`toast toast--${type} ${isClosing ? "toast--closing" : "toast--enter"}`}
      role="status"
      aria-live="polite"
    >
      <button
        type="button"
        className="toast__closeButton"
        aria-label="Dismiss notification"
        onClick={closeToast}
      >
        ×
      </button>
      <div className="toast__message">{message}</div>
      <div className="toast__progress" style={progressStyle} aria-hidden />
    </div>
  );
};

export default Toast;