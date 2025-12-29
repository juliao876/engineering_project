import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/SettingsPage.css";
import "../styles/tokens.css";

import Sidebar from "../components/Sidebar.tsx";
import Navbar from "../components/Navbar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";
import Input from "../components/Input.tsx";
import Button from "../components/Button.tsx";

import SwitchOff from "../assets/icons/Switch-Off.svg";
import SwitchOn from "../assets/icons/Switch-On.svg";
import ProfileImage from "../assets/images/Profile.png";

import { AuthAPI } from "../services/api.ts";
import { saveUserSettings } from "../services/userSettings.ts";
import { useToast } from "../components/ToastProvider.tsx";
import useSidebarNavigation from "../hooks/useSidebarNavigation.ts";

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
  const [avatarUrl, setAvatarUrl] = useState<string>("");
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
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
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const [showFigmaHelpModal, setShowFigmaHelpModal] = useState(false);
  const [isFigmaHelpClosing, setIsFigmaHelpClosing] = useState(false);

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
        setBioText(data?.bio || "");
        setBioEnabled(Boolean(data?.bio));
        setFigmaClientId(data?.figma_client_id || "");
        setFigmaClientSecret(data?.figma_client_secret || "");
        setAvatarUrl(data?.avatar_url || "");
        saveUserSettings({
          bioEnabled: Boolean(data?.bio),
          bioText: data?.bio || "",
          figmaClientId: data?.figma_client_id || "",
          figmaClientSecret: data?.figma_client_secret || "",
          avatarUrl: data?.avatar_url || "",
        });
      }
    };
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

  const handleSidebarSelect = useSidebarNavigation({
    openSearch: () => setIsSearchOpen(true),
  });

  const handleSave = async () => {
    setIsSavingProfile(true);
    setStatusMessage(null);
    const payload: Record<string, string> = {};
    if (name !== undefined) payload.name = name;
    if (surname !== undefined) payload.family_name = surname;
    if (username !== undefined) payload.username = username;
    if (email !== undefined) payload.email = email;
    payload.bio = bioEnabled ? bioText : "";
    payload.figma_client_id = figmaClientId;
    payload.figma_client_secret = figmaClientSecret;

    const response = await AuthAPI.updateMe(payload);

    if (response.ok) {
      const updated = response.data;
      setUser(updated);
      setAvatarUrl(updated?.avatar_url || avatarUrl);
      saveUserSettings({
        bioEnabled: !!payload.bio,
        bioText: payload.bio,
        figmaClientId,
        figmaClientSecret,
        avatarUrl: updated?.avatar_url || avatarUrl,
      });
      setStatusMessage("Settings saved. Your profile and Figma flows will use these values.");
    } else {
      const detail =
        (response.data && (response.data.detail || response.data.message)) ||
        "Unable to save profile changes.";
      setStatusMessage(detail);
    }
    setIsSavingProfile(false);
  };

  const handleAvatarUpload = async (file: File) => {
    setIsUploadingAvatar(true);
    const response = await AuthAPI.uploadAvatar(file);
    if (response.ok) {
      const updated = response.data;
      setAvatarUrl(updated?.avatar_url || "");
      setUser(updated);
      saveUserSettings({
        bioEnabled: bioEnabled,
        bioText,
        figmaClientId,
        figmaClientSecret,
        avatarUrl: updated?.avatar_url || "",
      });
      addToast({ message: "Profile photo updated", type: "success" });
    } else {
      addToast({
        message: response.data?.detail || "Could not upload profile photo.",
        type: "error",
      });
    }
    setIsUploadingAvatar(false);
  };

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    void handleAvatarUpload(file);
  };

  const openAvatarPicker = () => {
    avatarInputRef.current?.click();
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

  const openFigmaHelpModal = () => {
    setShowFigmaHelpModal(true);
  };

  const closeFigmaHelpModal = () => {
    setIsFigmaHelpClosing(true);
    setTimeout(() => {
      setShowFigmaHelpModal(false);
      setIsFigmaHelpClosing(false);
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
              <div
                className="settings-page__avatarMask"
                style={{ backgroundImage: `url(${avatarUrl || ProfileImage})` }}
                aria-label="Profile avatar"
              />
            </div>
            <div className="settings-page__upload">
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/*"
                style={{ display: "none" }}
                onChange={handleAvatarChange}
              />
              <Button variant="secondary" size="medium" onClick={openAvatarPicker} disabled={isUploadingAvatar}>
                {isUploadingAvatar ? "Uploading..." : "Upload Profile Picture"}
              </Button>
              <p className="settings-page__helper">Profile photo will follow your portfolio mask.</p>
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
            Use your own Figma OAuth app credentials to import designs. The credentials are saved to your account for reuse.
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
            <Button variant="primary" size="medium" onClick={openFigmaHelpModal}>
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
                  enablePasswordToggle
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
                <Input
                  label="New password"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  enablePasswordToggle
                  onChange={(e) => setNewPassword(e.target.value)}
                />
                <Input
                  label="Repeat new password"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  enablePasswordToggle
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
        {showFigmaHelpModal && (
          <div
            className={`settings-page__modalOverlay ${isFigmaHelpClosing ? "is-closing" : ""}`}
            onClick={closeFigmaHelpModal}
          >
            <div
              className={`settings-page__modalCard ${isFigmaHelpClosing ? "is-exit" : "is-open"}`}
              onClick={(e) => e.stopPropagation()}
            >
              <button className="settings-page__modalClose" onClick={closeFigmaHelpModal}>
                ×
              </button>

              <h3 className="settings-page__modalTitle">
                How to get Figma credentials
              </h3>

              <p className="settings-page__modalSubtitle">
                Follow these steps to create your own Figma OAuth app.
              </p>

              <ol className="settings-page__figmaSteps">
                <li>
                  Go to{" "}
                  <a href="https://www.figma.com/developers/apps" target="_blank" rel="noreferrer">
                    figma.com/developers/apps
                  </a>
                </li>
                <li>Click <strong>Create a new app</strong>.</li>
                <li>Set app name to <strong>Uinside analyzer</strong>.</li>
                <li>
                  Callback URL:
                  <br />
                  <a
                    href="http://localhost:3000/figma/callback"
                    target="_blank"
                    rel="noreferrer"
                    className="settings-page__callbackLink"
                  >
                    http://localhost:3000/figma/callback
                  </a>
                </li>
                <li>Copy Client ID and Client Secret.</li>
                <li><strong>Important:</strong> Client Secret is shown only once.</li>
              </ol>

              <div className="settings-page__modalActions">
                <Button variant="primary" size="medium" onClick={closeFigmaHelpModal}>
                  Got it
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