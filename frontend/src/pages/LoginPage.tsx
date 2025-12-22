import React, { useState } from "react";
import "../styles/LoginPage.css";
import "../styles/tokens.css";

import Input from "../components/Input.tsx";
import Button from "../components/Button.tsx";

import Eyecon from "../assets/icons/Eyecon.png";
import Logo from "../assets/icons/Logo.svg";
import LoginImage from "../assets/images/LoginImage.png";

import { AuthAPI, NotificationsAPI } from "../services/api.ts";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider.tsx";

const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const { addToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      login: emailOrUsername,
      password,
    };

    const res = await AuthAPI.login(payload);

    if (res.ok) {
      const receivedToken = (res.data && (res.data.token || res.data["token"])) as string | undefined;
      if (receivedToken) {
        localStorage.setItem("token", receivedToken);
      }
      addToast({ message: "Successfully logged in", type: "success" });
      setTimeout(async () => {
        const notifications = await NotificationsAPI.getNotifications();
        if (notifications.ok && Array.isArray(notifications.data)) {
          const unread = notifications.data.filter((item: any) => !item.is_read).length;
          if (unread > 0) {
            const capped = unread > 99 ? "99+" : unread.toString();
            addToast({ message: `You have ${capped} unread notifications`, type: "info" });
          }
        }
        navigate("/profile");
      }, 500);
    } else {
      addToast({
        message: res.data?.detail || res.data?.message || "Login failed",
        type: "error",
      });
    }
  };

  return (
    <div className="login-page">
      <header className="login-page__nav">
        <div className="login-page__brand">
          <img src={Logo} alt="uinside logo" className="login-page__brandIcon" />
        </div>
      </header>

      <div className="login-page__content">
        <div className="login-page__card">
          <h1 className="login-page__title">Log in</h1>

          <form className="login-page__form" onSubmit={handleSubmit}>
            <Input
              placeholder="Email or username"
              value={emailOrUsername}
              onChange={(e) => setEmailOrUsername(e.target.value)}
              required
            />

            <Input
              placeholder="Password"
              type="password"
              icon={<img src={Eyecon} alt="" />}
              iconPosition="right"
              enablePasswordToggle
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" variant="primary" size="medium" fullWidth>
              Sign in
            </Button>
          </form>

          <div className="login-page__switch">
            <span className="login-page__switchText">Don't have an account?</span>
            <Button
              type="button"
              variant="secondary"
              size="small"
              onClick={() => navigate("/register")}
              className="login-page__switchButton"
            >
              Register
            </Button>
          </div>
        </div>

        <div className="login-page__illustration">
          <img src={LoginImage} alt="Login illustration" />
        </div>
      </div>
    </div>
  );
};

export default LoginPage;