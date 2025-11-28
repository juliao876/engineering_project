import React, { useEffect, useState } from "react";
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

  useEffect(() => {
    if (!duration) return;
    const closeTimer = setTimeout(() => {
      setIsClosing(true);
    }, duration);

    const cleanupTimer = setTimeout(() => {
      onClose?.();
    }, duration + exitAnimationDuration);

    return () => {
      clearTimeout(closeTimer);
      clearTimeout(cleanupTimer);
    };
  }, [duration, exitAnimationDuration, onClose]);

  const progressStyle: React.CSSProperties & { ["--toast-duration"]?: string } = {
    "--toast-duration": `${duration}ms`,
  };

  return (
    <div
      className={`toast toast--${type} ${isClosing ? "toast--closing" : "toast--enter"}`}
      role="status"
      aria-live="polite"
    >
      <div className="toast__message">{message}</div>
      <div className="toast__progress" style={progressStyle} aria-hidden />
    </div>
  );
};

export default Toast;