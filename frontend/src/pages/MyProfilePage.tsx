import React, { useEffect, useMemo, useState } from "react";
import "../styles/MyProfilePage.css";
import "../styles/tokens.css";

import ProfileImage from "../assets/images/Profile.png";
import StarEmptyIcon from "../assets/icons/StarEmpty-Icon.svg";
import StarFullIcon from "../assets/icons/StarFull-Icon.svg";

import Sidebar, { SidebarItemId } from "../components/Sidebar.tsx";
import ProjectCard from "../components/ProjectCard.tsx";
import Button from "../components/Button.tsx";
import Navbar from "../components/Navbar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";

import { AuthAPI, ProjectsAPI } from "../services/api.ts";
import { useNavigate } from "react-router-dom";
import { loadUserSettings } from "../services/userSettings.ts";

const MyProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // ====== STATE UŻYTKOWNIKA ======
  const [user, setUser] = useState<any>(null);

  // ====== STATE PROJEKTÓW ======
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isModalClosing, setIsModalClosing] = useState(false);

  const closeModalWithAnimation = () => {
    setIsModalClosing(true);
    setTimeout(() => {
      setIsModalVisible(false);
      setSelectedProject(null);
      setIsModalClosing(false);
    }, 420);
  };

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

  // ====== ŁADOWANIE DANYCH ======
  useEffect(() => {
    async function loadData() {
      // 1. POBIERAMY DANE UŻYTKOWNIKA
      const me = await AuthAPI.me();

      if (me.ok) {
        setUser(me.data);
      } else {
        console.log("Failed to load user profile", me.data);
        if (me.status === 401) navigate("/login");
      }

      // 2. POBIERAMY PROJEKTY
      const myProjects = await ProjectsAPI.getMyProjects();

      if (myProjects.ok) {
        const projectsData = myProjects.data?.projects ?? myProjects.data ?? [];
        setProjects(projectsData);
      } else {
        console.log("Failed to load projects", myProjects.data);
      }
    }

    loadData();
  }, [navigate]);

  const displayName = user
    ? [user.name, user.family_name].filter(Boolean).join(" ") || user.username
    : "Loading...";

  const displayUsername = user ? user.username : "";

  const userSettings = useMemo(() => loadUserSettings(), []);
  const customBio =
    userSettings.bioEnabled && userSettings.bioText.trim().length > 0
      ? userSettings.bioText.trim()
      : null;

  const renderStars = (value: number) => {
    return Array.from({ length: 5 }, (_, index) => {
      const filled = index < value;
      const Icon = filled ? StarFullIcon : StarEmptyIcon;
      return <img key={index} src={Icon} alt={filled ? "Filled star" : "Empty star"} />;
    });
  };

  return (
    <div className="profile-page">
      {/* SIDEBAR */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        activeItem="profile"
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

      {/* MAIN */}
      <main className="profile-page__main">
        {/* HERO */}
        <section className="profile-page__hero">
          <div className="profile-page__heroImageWrapper">
            <img src={ProfileImage} alt="Profile gradient" />
          </div>

          <div className="profile-page__heroContent">
            <p className="profile-page__heroLabel">I AM</p>

            <h1 className="profile-page__heroName">{displayName}</h1>

            <h2 className="profile-page__heroRole">{displayUsername}</h2>

            <p className="profile-page__heroBio">
              {user
                ? customBio ||
                  user.bio ||
                  "This user has not added a bio yet. You can update this in Settings."
                : ""}
            </p>
          </div>
        </section>

        {/* PROJECT GRID */}
        <section className="profile-page__projects">
          <div className="profile-page__projectsGrid">
            {projects.length > 0 ? (
              projects.map((project, index) => (
                <ProjectCard
                  key={index}
                  title={project.title}
                  description={project.description || ""}
                  rating={project.rating || 0}
                  commentsCount={project.comments || 0}
                  figmaUrl={project.figma_link}
                  previewUrl={project.preview_url}
                  contentType={project.contents}
                  onPreviewClick={() => {
                    setSelectedProject(project);
                    setIsModalVisible(true);
                    setIsModalClosing(false);
                  }}
                />
              ))
            ) : (
              <p style={{ textAlign: "center", width: "100%", color: "#666" }}>
                No projects yet.
              </p>
            )}
          </div>

          <div className="profile-page__createWrapper">
            <Button variant="secondary" size="medium" onClick={() => navigate("/projects/create") }>
              Create new Project
            </Button>
          </div>
        </section>
      </main>

      <div className="profile-page__bottomGradient" />

      {isModalVisible && selectedProject && (
        <div
          className={`profile-page__overlay ${isModalClosing ? "is-closing" : ""}`}
          role="dialog"
          aria-modal="true"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              closeModalWithAnimation();
            }
          }}
        >
          <div
            className={`profile-page__detailsModal ${isModalClosing ? "is-closing" : ""}`}
          >
            <button
              type="button"
              className="profile-page__figmaClose"
              aria-label="Close"
              onClick={closeModalWithAnimation}
            >
              ×
            </button>

            <div className="profile-page__detailsGrid">
              <div className="profile-page__detailsMedia">
                {selectedProject.preview_url ? (
                  <img src={selectedProject.preview_url} alt={`${selectedProject.title} preview`} />
                ) : (
                  <div className="profile-page__figmaPlaceholder" />
                )}
              </div>

              <div className="profile-page__detailsBody">
                <div className="profile-page__figmaHeader">
                  <div>
                    <p className="profile-page__figmaEyebrow">Project details</p>
                    <h3>{selectedProject.title}</h3>
                    <p>{selectedProject.description}</p>
                  </div>
                  {selectedProject.figma_link && (
                    <a
                      className="profile-page__figmaAction"
                      href={selectedProject.figma_link}
                      target="_blank"
                      rel="noreferrer"
                    >
                      See it in Figma
                    </a>
                  )}
                </div>

                <div className="profile-page__figmaRating">{renderStars(selectedProject.rating || 0)}</div>

                <div className="profile-page__commentsBlock">
                  <div className="profile-page__commentsHeader">
                    <h4>Comments</h4>
                    <Button variant="secondary" size="small">
                      Load more
                    </Button>
                  </div>
                  <ul className="profile-page__commentsList">
                    {(selectedProject.comments_list || []).length > 0 ? (
                      (selectedProject.comments_list || []).map((comment: any, idx: number) => (
                        <li key={idx} className="profile-page__commentRow">
                          <div className="profile-page__commentAvatar" aria-hidden>
                            {comment.author?.[0] || "?"}
                          </div>
                          <div>
                            <p className="profile-page__commentAuthor">{comment.author || "Anonymous"}</p>
                            <p className="profile-page__commentText">{comment.text}</p>
                          </div>
                        </li>
                      ))
                    ) : (
                      <li className="profile-page__commentEmpty">No comments yet.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyProfilePage;