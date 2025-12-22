
import React, { useState } from "react";
import "../styles/RegisterPage.css";
import "../styles/tokens.css";

import Input from "../components/Input.tsx";
import Button from "../components/Button.tsx";

import Eyecon from "../assets/icons/Eyecon.png";
import Logo from "../assets/icons/Logo.svg";
import RegisterImage from "../assets/images/RegisterImage.png";

import { AuthAPI } from "../services/api.ts";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider.tsx";

const RegisterPage: React.FC = () => {
    const navigate = useNavigate();

    const [name, setName] = useState("");
    const [surname, setSurname] = useState("");
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const { addToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      name,
      family_name: surname,
      username,
      email,
      password,
    };

    const res = await AuthAPI.register(payload);

    if (res.ok) {
      addToast({
        message: "Account created! Please log in.",
        type: "success",
      });
      setTimeout(() => navigate("/login"), 500);
      return;
    }

    // 🔴 TU JEST NOWA LOGIKA
    const detail = res.data?.detail || res.data?.message || "";

    if (typeof detail === "string") {
      if (detail.toLowerCase().includes("username")) {
        addToast({
          message: "This username is already taken",
          type: "error",
        });
        return;
      }

      if (detail.toLowerCase().includes("email")) {
        addToast({
          message: "This email is already registered",
          type: "error",
        });
        return;
      }
    }
    addToast({
      message: "Registration failed. Please try again.",
      type: "error",
    });
  };


  return (
    <div className="register-page">
      <header className="register-page__nav">
        <div className="register-page__brand">
          <img src={Logo} alt="uinside logo" className="register-page__brandIcon" />
        </div>
      </header>

      <div className="register-page__content">
        <div className="register-page__illustration">
          <img src={RegisterImage} alt="Register illustration" />
        </div>

        <div className="register-page__card">
          <h1 className="register-page__title">Register</h1>

          <form className="register-page__form" onSubmit={handleSubmit}>
            <Input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <Input placeholder="Surname" value={surname} onChange={(e) => setSurname(e.target.value)} required />
            <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
            <Input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input
              placeholder="Password"
              type="password"
              icon={<img src={Eyecon} alt="" aria-hidden />}
              iconPosition="right"
              enablePasswordToggle
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" variant="primary" size="medium" fullWidth>
              Sign up
            </Button>
          </form>

          <div className="register-page__switch">
            <span className="register-page__switchText">Already have an account?</span>
            <Button
              type="button"
              variant="secondary"
              size="small"
              onClick={() => navigate("/login")}
              className="register-page__switchButton"
            >
              Log in
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;