import React from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import WelcomePage from './pages/WelcomePage.tsx';
import LoginPage from './pages/LoginPage.tsx';
import RegisterPage from './pages/RegisterPage.tsx';
import MyProfilePage from './pages/MyProfilePage.tsx';

// Most important wrapper
function WelcomeWithNavigation() {
  const navigate = useNavigate();
  return (
    <WelcomePage
      onRegisterClick={() => navigate("/register")}
      onLoginClick={() => navigate("/login")}
    />
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<WelcomeWithNavigation />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/profile" element={<MyProfilePage />} />
    </Routes>
  );
}

export default App;