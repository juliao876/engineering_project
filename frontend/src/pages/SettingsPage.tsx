import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/SettingsPage.css";
import "../styles/tokens.css";

import Sidebar, { SidebarItemId } from "../components/Sidebar.tsx";
import Navbar from "../components/Navbar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";
import Input from "../components/Input.tsx";
import Button from "../components/Button.tsx";

import SwitchOff from "../assets/icons/Switch-Off.svg";
import SwitchOn from "../assets/icons/Switch-On.svg";
import ProfileImage from "../assets/images/Profile.png";

import { AuthAPI } from "../services/api.ts";
import { loadUserSettings, saveUserSettings } from "../services/userSettings.ts";
import { useToast } from "../components/ToastProvider.tsx";

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [user, setUser] = useState<any>(null);
  const [name, setName] = useState("");
  const [surname, setSurname] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [isPasswordModalClosing, setIsPasswordModalClosing] = useState(false);
  const [bioText, setBioText] = useState("");
  const [bioEnabled, setBioEnabled] = useState(false);
  const [figmaClientId, setFigmaClientId] = useState("");
  const [figmaClientSecret, setFigmaClientSecret] = useState("");

  useEffect(() => {
    const load = async () => {
      const response = await AuthAPI.me();
      if (response.ok) {
        const data = response.data;
        setUser(data);
        setName(data?.name || "");
        setSurname(data?.family_name || "");
        setUsername(data?.username || "");
        setEmail(data?.email || "");
      }
    };
    const stored = loadUserSettings();
    setBioText(stored.bioText || "");
    setBioEnabled(stored.bioEnabled);
    setFigmaClientId(stored.figmaClientId || "");
    setFigmaClientSecret(stored.figmaClientSecret || "");

    void load();
  }, []);

  const fullName = useMemo(
    () => [name, surname].filter(Boolean).join(" "),
    [name, surname]
  );

  const handleLogout = async () => {
    await AuthAPI.logout();
    localStorage.removeItem("token");
    navigate("/login");
  };

  const handleSidebarSelect = (itemId: SidebarItemId) => {
    switch (itemId) {
      case "profile":
        navigate("/profile");
        break;
      case "create":
        navigate("/projects/create");
        break;
      case "home":
        navigate("/");
        break;
      case "search":
        setIsSearchOpen(true);
        break;
      case "settings":
        navigate("/settings");
        break;
      default:
        break;
    }
  };

  const handleSave = async () => {
    saveUserSettings({
      bioEnabled,
      bioText,
      figmaClientId,
      figmaClientSecret,
    });

    setIsSavingProfile(true);
    setStatusMessage(null);
    const payload: Record<string, string> = {};
    if (name !== undefined) payload.name = name;
    if (surname !== undefined) payload.family_name = surname;
    if (username !== undefined) payload.username = username;
    if (email !== undefined) payload.email = email;

    const response = await AuthAPI.updateMe(payload);

    if (response.ok) {
      setStatusMessage("Settings saved. Your profile and Figma flows will use these values.");
    } else {
      const detail =
        (response.data && (response.data.detail || response.data.message)) ||
        "Unable to save profile changes.";
      setStatusMessage(detail);
    }
    setIsSavingProfile(false);
  };

  const handleUpdatePassword = async () => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      addToast({ message: "Fill in all password fields.", type: "error" });
      return;
    }

    if (newPassword !== confirmPassword) {
      addToast({ message: "New passwords do not match.", type: "error" });
      return;
    }

    setIsUpdatingPassword(true);
    const response = await AuthAPI.updateMe({
      current_password: currentPassword,
      new_password: newPassword,
    });

    if (response.ok) {
      addToast({ message: "Password updated successfully.", type: "success" });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setIsPasswordModalClosing(true);
      setTimeout(() => {
        setShowPasswordModal(false);
        setIsPasswordModalClosing(false);
      }, 320);
    } else {
      const detail =
        (response.data && (response.data.detail || response.data.message)) ||
        "Unable to update password.";
      addToast({ message: detail || "Wrong password.", type: "error" });
    }
    setIsUpdatingPassword(false);
  };

  const openPasswordModal = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setShowPasswordModal(true);
  };

  const closePasswordModal = () => {
    setIsPasswordModalClosing(true);
    setTimeout(() => {
      setShowPasswordModal(false);
      setIsPasswordModalClosing(false);
    }, 320);
  };

  return (
    <div className="settings-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onSelect={handleSidebarSelect}
        onLogout={handleLogout}
        activeItem="settings"
      />

      <Navbar onMenuClick={() => setIsSidebarOpen(true)} />

      <SearchOverlay
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onNavigateToUser={(userName) => navigate(`/users/${userName}`)}
      />

      <main className="settings-page__content">
        <header className="settings-page__header">
          <div>
            <p className="settings-page__eyebrow">Settings</p>
            <h1 className="settings-page__title">Account settings</h1>
            {statusMessage && <p className="settings-page__status">{statusMessage}</p>}
          </div>
          <Button variant="primary" size="medium" onClick={handleSave} disabled={isSavingProfile}>
            Save
          </Button>
        </header>

        <section className="settings-page__card">
          <div className="settings-page__sectionHeader">
            <p className="settings-page__sectionEyebrow">Settings</p>
            <h2 className="settings-page__sectionTitle">Profile setup</h2>
          </div>

          <div className="settings-page__profileBlock">
            <div className="settings-page__avatar">
              <img src={ProfileImage} alt="Profile placeholder" />
            </div>
            <div className="settings-page__upload">
              <Button variant="secondary" size="medium">Upload Profile Picture</Button>
              <p className="settings-page__helper">Profile photo size</p>
            </div>
          </div>

          <div className="settings-page__bio">
            <div className="settings-page__bioHeader">
              <span className="settings-page__bioLabel">Bio</span>
              <button
                type="button"
                className="settings-page__switch"
                onClick={() => setBioEnabled((prev) => !prev)}
                aria-label={bioEnabled ? "Disable bio" : "Enable bio"}
              >
                <img src={bioEnabled ? SwitchOn : SwitchOff} alt="Toggle bio" />
              </button>
            </div>
            <textarea
              className="settings-page__textarea"
              placeholder="This user has not added a bio yet"
              value={bioText}
              onChange={(event) => setBioText(event.target.value)}
              disabled={!bioEnabled}
            />
          </div>
        </section>

        <section className="settings-page__card">
          <div className="settings-page__sectionHeader">
            <p className="settings-page__sectionEyebrow">Settings</p>
            <h2 className="settings-page__sectionTitle">User setup</h2>
          </div>

          <div className="settings-page__grid">
            <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} />
            <Input label="Surname" value={surname} onChange={(e) => setSurname(e.target.value)} />
            <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>

          <div className="settings-page__summary">
            <p className="settings-page__summaryName">{fullName || "Your name"}</p>
            <p className="settings-page__summaryUser">{username || user?.username || "@username"}</p>
          </div>

          <div className="settings-page__actions">
            <Button variant="secondary" size="medium" onClick={openPasswordModal} disabled={isUpdatingPassword}>
              Update password
            </Button>
          </div>
        </section>

        <section className="settings-page__card settings-page__figma">
          <div className="settings-page__sectionHeader">
            <p className="settings-page__sectionEyebrow">Settings</p>
            <h2 className="settings-page__sectionTitle">Figma setup</h2>
          </div>

          <p className="settings-page__helper">
            Use your own Figma OAuth app credentials to import designs. These values stay in your browser.
          </p>

          <div className="settings-page__grid">
            <Input
              label="Figma Client ID"
              value={figmaClientId}
              onChange={(e) => setFigmaClientId(e.target.value)}
              placeholder="Enter your Client ID"
            />
            <Input
              label="Figma Secret Key"
              value={figmaClientSecret}
              onChange={(e) => setFigmaClientSecret(e.target.value)}
              placeholder="Enter your Secret Key"
              type="password"
            />
          </div>

          <div className="settings-page__actions">
            <Button variant="primary" size="medium" onClick={() => {}}>
              Let us help
            </Button>
          </div>
        </section>

        {showPasswordModal && (
          <div
            className={`settings-page__modalOverlay ${isPasswordModalClosing ? "is-closing" : ""}`}
            role="presentation"
            onClick={closePasswordModal}
          >
            <div
              className={`settings-page__modalCard ${isPasswordModalClosing ? "is-exit" : "is-open"}`}
              role="dialog"
              aria-modal="true"
              aria-labelledby="settings-password-title"
              onClick={(e) => e.stopPropagation()}
            >
              <button className="settings-page__modalClose" aria-label="Close" onClick={closePasswordModal}>
                ×
              </button>
              <h3 className="settings-page__modalTitle" id="settings-password-title">
                Update password
              </h3>
              <p className="settings-page__modalSubtitle">
                Enter your current password and choose a new one.
              </p>
              <div className="settings-page__modalGrid">
                <Input
                  label="Current password"
                  type="password"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
                <Input
                  label="New password"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <Input
                  label="Repeat new password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>

              <div className="settings-page__modalActions">
                <Button variant="secondary" size="medium" onClick={closePasswordModal} disabled={isUpdatingPassword}>
                  Cancel
                </Button>
                <Button variant="primary" size="medium" onClick={handleUpdatePassword} disabled={isUpdatingPassword}>
                  Save password
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default SettingsPage;