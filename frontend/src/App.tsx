import React from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import Cursor from "./components/Cursor.tsx";

import WelcomePage from './pages/WelcomePage.tsx';
import LoginPage from './pages/LoginPage.tsx';
import RegisterPage from './pages/RegisterPage.tsx';
import MyProfilePage from './pages/MyProfilePage.tsx';
import CreateProjectPage from "./pages/CreateProjectPage.tsx";
import UserProfilePage from "./pages/UserProfilePage.tsx";
import FigmaCallbackPage from "./pages/FigmaCallbackPage.tsx";
import SettingsPage from "./pages/SettingsPage.tsx";
import AnalysisPage from "./pages/AnalysisPage.tsx";
import DiscoverPage from "./pages/DiscoverPage.tsx";

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
    <>
      <Cursor />
      <Routes>
        <Route path="/" element={<WelcomeWithNavigation />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile" element={<MyProfilePage />} />
        <Route path="/projects/create" element={<CreateProjectPage />} />
        <Route path="/users/:username" element={<UserProfilePage />} />
        <Route path="/figma/callback" element={<FigmaCallbackPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/analysis/:projectId" element={<AnalysisPage />} />
        <Route path="/discover" element={<DiscoverPage />} />
      </Routes>
    </>
  );
}

export default App;