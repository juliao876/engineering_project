import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import CheckboxOff from "../assets/icons/Checkbox-Off.svg";
import CheckboxOn from "../assets/icons/Checkbox-On.svg";
import SwitchOff from "../assets/icons/Switch-Off.svg";
import SwitchOn from "../assets/icons/Switch-On.svg";
import CloseIcin from "../assets/icons/CloseIcin.svg";
import FigmaProjectIcon from "../assets/images/Figma-Project.png";
import ImageProjectIcon from "../assets/images/Image-Project.png";
import VideoProjectIcon from "../assets/images/Video-Project.png";
import ProjectImage from "../assets/images/ProjectImage.png";
import "../styles/CreateProjectPage.css";
import "../styles/tokens.css";
import Button from "../components/Button.tsx";
import Sidebar, { SidebarItemId } from "../components/Sidebar.tsx";
import Navbar from "../components/Navbar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";
import { AuthAPI, ProjectsAPI, FigmaAPI } from "../services/api.ts";
import { loadUserSettings } from "../services/userSettings.ts";

type ProjectType = "figma" | "image" | "video";

const projectOptions: { key: ProjectType; label: string; helper: string; icon: string }[] = [
  { key: "figma", label: "Figma", helper: "Import from a Figma link", icon: FigmaProjectIcon },
  { key: "image", label: "Image", helper: "Upload a design snapshot", icon: ImageProjectIcon },
  { key: "video", label: "Video", helper: "Share a design walk-through", icon: VideoProjectIcon },
];

const CreateProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [showTypeModal, setShowTypeModal] = useState<boolean>(() => location.state?.openTypeModal ?? true);
  const [isModalClosing, setIsModalClosing] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(showTypeModal);
  const [selectedType, setSelectedType] = useState<ProjectType>("figma");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [figmaLink, setFigmaLink] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isPublic, setIsPublic] = useState(false);
  const [figmaPreview, setFigmaPreview] = useState<string | null>(null);
  const [figmaPreviewLoading, setFigmaPreviewLoading] = useState(false);
  const [figmaImportData, setFigmaImportData] = useState<any | null>(null);
  const [lastFetchedFigmaLink, setLastFetchedFigmaLink] = useState<string>("");
  const [figmaConnected, setFigmaConnected] = useState<boolean>(
    () => localStorage.getItem("figma_connected") === "true"
  );
  const [figmaStateToken, setFigmaStateToken] = useState<string | null>(
    () => localStorage.getItem("figma_oauth_state")
  );
  const [connectingFigma, setConnectingFigma] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const currentSource = useMemo(
    () => projectOptions.find((opt) => opt.key === selectedType),
    [selectedType]
  );

  const previewUrl = useMemo(() => {
    if (uploadFile && selectedType !== "figma") {
      return URL.createObjectURL(uploadFile);
    }
    return null;
  }, [uploadFile, selectedType]);

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

  useEffect(() => {
    setShowTypeModal(location.state?.openTypeModal ?? true);
  }, [location.state]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get("figma") === "connected") {
      setFigmaConnected(true);
      localStorage.setItem("figma_connected", "true");
      setStatusMessage("Figma connected — paste a Figma file URL to import a preview.");
    }
  }, [location.search]);

  useEffect(() => {
    if (showTypeModal) {
      setIsModalVisible(true);
      setIsModalClosing(false);
    } else if (isModalVisible) {
      setIsModalClosing(true);
      const timeout = setTimeout(() => {
        setIsModalVisible(false);
        setIsModalClosing(false);
      }, 450);
      return () => clearTimeout(timeout);
    }
  }, [showTypeModal, isModalVisible]);

  const resetFile = () => {
    setUploadFile(null);
  };

  const handleSelectType = (type: ProjectType) => {
    setSelectedType(type);
    setStatusMessage(null);
    setFigmaPreview(null);
    setLastFetchedFigmaLink("");
    if (type === "figma") {
      resetFile();
    } else {
      setFigmaLink("");
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadFile(file);
  };

  const handleStartFigmaConnect = async () => {
    const userSettings = loadUserSettings();
    setStatusMessage(null);
    setConnectingFigma(true);

    try {
      const response = await FigmaAPI.buildAuthUrl({
        clientId: userSettings.figmaClientId,
        clientSecret: userSettings.figmaClientSecret,
      });
      console.log("[Figma] Auth URL response", response);

      if (response.ok && response.data?.authorize_url) {
        if (response.data.state) {
          localStorage.setItem("figma_oauth_state", response.data.state);
          setFigmaStateToken(response.data.state);
        }
        window.location.href = response.data.authorize_url;
      } else {
        setStatusMessage(response.data?.detail || "Cannot start Figma authorization.");
      }
    } finally {
      setConnectingFigma(false);
    }
  };

  useEffect(() => {
    if (selectedType !== "figma") {
      setFigmaPreview(null);
      setFigmaImportData(null);
      setFigmaPreviewLoading(false);
      return;
    }

    const trimmedLink = figmaLink.trim();
    if (!trimmedLink) {
      setFigmaPreview(null);
      setFigmaImportData(null);
      setStatusMessage(null);
      return;
    }

    if (!figmaConnected) {
      setStatusMessage("Connect your Figma account to fetch a preview.");
      return;
    }

    if (trimmedLink === lastFetchedFigmaLink) {
      return;
    }

    const timeout = setTimeout(async () => {
      setFigmaPreviewLoading(true);
      const response = await FigmaAPI.importFile({ file_url: trimmedLink });
      console.log("[Figma] Import/preview response", response);

      if (response.ok && response.data?.preview_url) {
        setFigmaPreview(response.data.preview_url);
        setFigmaImportData(response.data);
        setLastFetchedFigmaLink(trimmedLink);
        setStatusMessage(null);
      } else if (!response.ok) {
        setFigmaPreview(null);
        setFigmaImportData(null);
        setStatusMessage(response.data?.detail || "Could not load Figma preview.");
      }
      setFigmaPreviewLoading(false);
    }, 600);

    return () => clearTimeout(timeout);
  }, [figmaLink, lastFetchedFigmaLink, selectedType, figmaConnected]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setStatusMessage(null);

    if (!title.trim()) {
      setStatusMessage("Please provide a title for your project.");
      return;
    }

    if (selectedType === "figma" && !figmaLink.trim()) {
      setStatusMessage("Add a Figma link to import your design.");
      return;
    }

    if (selectedType === "figma" && !figmaConnected) {
      setStatusMessage("Connect your Figma account before importing a link.");
      return;
    }

    if ((selectedType === "image" || selectedType === "video") && !uploadFile) {
      setStatusMessage("Upload a file to continue.");
      return;
    }

    const form = new FormData();
    form.append("title", title);
    form.append("description", description);
    form.append("is_public", String(isPublic));
    form.append("contents", selectedType);
    form.append("content_type", uploadFile?.type || selectedType);

    if (selectedType === "figma") {
      form.append("figma_link", figmaLink);
      if (figmaImportData?.preview_url) {
        form.append("preview_url", figmaImportData.preview_url);
      }
    }

    if (uploadFile) {
      form.append("file", uploadFile);
    }

    try {
      setSubmitting(true);
      const response = await ProjectsAPI.createProject(form);
      console.log("[Projects] Create project response", response);
      if (response.ok) {
        console.log("[Projects] Created project payload", {
          title,
          description,
          selectedType,
          figmaLink: selectedType === "figma" ? figmaLink : undefined,
          isPublic,
          response: response.data,
        });
        navigate("/profile");
      } else {
        setStatusMessage(response.data?.detail || "Unable to create project.");
      }
    } catch (error) {
      setStatusMessage("Unexpected error while creating project.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="create-project-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        activeItem="create"
        onLogout={handleLogout}
        onSelect={handleSidebarSelect}
      />

      <Navbar
        onMenuClick={() => setIsSidebarOpen(true)}
      />

      <SearchOverlay
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onNavigateToUser={(username) => navigate(`/users/${username}`)}
      />

      {isModalVisible && (
        <div className={`create-project-page__modalOverlay ${isModalClosing ? "is-closing" : ""}`}>
          <div className={`create-project-page__modalCard ${showTypeModal ? "is-open" : "is-exit"}`}>
            <button
              type="button"
              className="create-project-page__modalClose"
              aria-label="Close"
              onClick={() => setShowTypeModal(false)}
            >
              <img src={CloseIcin} alt="Close" />
            </button>

            <h2 className="create-project-page__modalTitle">Lets Create New Project</h2>
            <p className="create-project-page__modalSubtitle">
              Choose the type of project you want to share in your profile
            </p>

            <div className="create-project-page__options create-project-page__options--modal">
              {projectOptions.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  className={`create-project-page__option ${selectedType === option.key ? "is-active" : ""}`}
                  onClick={() => handleSelectType(option.key)}
                >
                  <img src={option.icon} alt="" className="create-project-page__optionImage" />
                  <div className="create-project-page__optionMeta">
                    <span className="create-project-page__optionLabel">{option.label}</span>
                    <span className="create-project-page__optionHelper">{option.helper}</span>
                  </div>
                  <img
                    src={selectedType === option.key ? CheckboxOn : CheckboxOff}
                    alt={selectedType === option.key ? "Selected" : "Not selected"}
                    className="create-project-page__optionCheck"
                  />
                </button>
              ))}
            </div>

            <div className="create-project-page__modalActions">
              <Button variant="primary" size="large" type="button" onClick={() => setShowTypeModal(false)}>
                Continue
              </Button>
            </div>
          </div>
        </div>
      )}

      <main className="create-project-page__content">
        <div className="create-project-page__top">
          <section className="create-project-page__formWrapper">
            <div className="create-project-page__formHeader">
              <div>
                <p className="create-project-page__formEyebrow">Project details</p>
                <h3 className="create-project-page__formTitle">Share a new project</h3>
              </div>
              <Button variant="ghost" size="small" type="button" onClick={() => setShowTypeModal(true)}>
                Change project source
              </Button>
            </div>

            <form className="create-project-page__form" onSubmit={handleSubmit}>
              <div className="create-project-page__currentSource">
                <img
                  src={currentSource?.icon || ""}
                  alt="Current source"
                  className="create-project-page__currentSourceIcon"
                />
                <div>
                  <p className="create-project-page__currentSourceLabel">Current source</p>
                  <p className="create-project-page__currentSourceValue">{selectedType}</p>
                </div>
              </div>

              <label className="create-project-page__field">
                <span>Title</span>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="My new idea"
                  required
                />
              </label>

              <label className="create-project-page__field">
                <span>Description</span>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Tell us more about your project"
                />
              </label>

              {selectedType === "figma" ? (
                <div className="create-project-page__field create-project-page__field--figma">
                  <div className="create-project-page__fieldHeader">
                    <span>Figma Link</span>
                    <div className="create-project-page__figmaConnectRow">
                      <span
                        className={`create-project-page__figmaStatus ${figmaConnected ? "is-connected" : "is-disconnected"}`}
                      >
                        {figmaConnected ? "Connected" : "Not connected"}
                      </span>
                      <button
                        type="button"
                        onClick={handleStartFigmaConnect}
                        className="create-project-page__figmaConnectButton"
                        disabled={connectingFigma}
                      >
                        {connectingFigma
                          ? "Opening..."
                          : figmaConnected
                          ? "Reconnect Figma"
                          : "Connect Figma"}
                      </button>
                    </div>
                  </div>
                  <input
                    type="url"
                    value={figmaLink}
                    onChange={(e) => setFigmaLink(e.target.value)}
                    placeholder="https://www.figma.com/file/"
                    required
                  />
                  {figmaStateToken && (
                    <p className="create-project-page__figmaHint">State: {figmaStateToken}</p>
                  )}
                </div>
              ) : (
                <label className="create-project-page__field">
                  <span>Upload File</span>
                  <div className="create-project-page__fileInput">
                    <input type="file" accept={selectedType === "image" ? "image/*" : "video/*"} onChange={handleFileChange} />
                    {uploadFile && <p className="create-project-page__fileName">{uploadFile.name}</p>}
                  </div>
                </label>
              )}

              <label className="create-project-page__toggle" onClick={() => setIsPublic((prev) => !prev)}>
                <img
                  src={isPublic ? SwitchOn : SwitchOff}
                  alt={isPublic ? "Public" : "Private"}
                  className="create-project-page__toggleIcon"
                />
                <span>Public</span>
              </label>

              {statusMessage && <p className="create-project-page__status">{statusMessage}</p>}

              <Button type="submit" variant="primary" size="large" disabled={submitting}>
                {submitting ? "Sharing..." : "Share Project"}
              </Button>
            </form>
          </section>

          <div className="create-project-page__hero">
            <img src={ProjectImage} alt="Project" className="create-project-page__heroImage" />
          </div>
        </div>

        <section className="create-project-page__previewPanel">
          <div className="create-project-page__previewHeader">
            <h3>Project Preview</h3>
            <button type="button" className="create-project-page__previewClose" aria-label="Close preview">
              <img src={CloseIcin} alt="Close preview" />
            </button>
          </div>

          <div className="create-project-page__previewBody">
            <div className="create-project-page__previewMedia">
              {selectedType === "figma" && figmaPreviewLoading ? (
                <div className="create-project-page__previewPlaceholder">Loading preview...</div>
              ) : figmaPreview ? (
                <img
                  src={figmaPreview}
                  alt="Figma preview"
                  className="create-project-page__previewMediaImage"
                />
              ) : previewUrl ? (
                selectedType === "video" ? (
                  <video src={previewUrl} controls className="create-project-page__previewMediaVideo" />
                ) : (
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="create-project-page__previewMediaImage"
                  />
                )
              ) : (
                <div className="create-project-page__previewPlaceholder">
                  <div className="create-project-page__previewPlaceholderMark" />
                </div>
              )}
            </div>

            <div className="create-project-page__previewDetails">
              <div className="create-project-page__previewTitleRow">
                <div>
                  <p className="create-project-page__previewEyebrow">Project Details</p>
                  <h4 className="create-project-page__previewTitle">{title || "Title"}</h4>
                  <p className="create-project-page__previewDescription">
                    {description || "Add a short description for your project."}
                  </p>
                </div>
                <Button variant="primary" size="small" type="button">
                  See it in Figma
                </Button>
              </div>
              <div className="create-project-page__previewMeta">
                {[1, 2, 3].map((item) => (
                  <div key={item} className="create-project-page__previewMetaRow">
                    <div className="create-project-page__previewAvatar" />
                    <div className="create-project-page__previewMetaText">
                      <strong>User Name</strong>
                      <p>Praesent facilisis mauris commodo enim.</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default CreateProjectPage;