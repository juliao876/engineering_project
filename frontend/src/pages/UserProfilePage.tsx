import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "../styles/MyProfilePage.css";
import "../styles/UserProfilePage.css";

import Navbar from "../components/Navbar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";
import Sidebar, { SidebarItemId } from "../components/Sidebar.tsx";
import Button from "../components/Button.tsx";
import ProjectCard from "../components/ProjectCard.tsx";

import ProfileImage from "../assets/images/Profile.png";
import StarEmptyIcon from "../assets/icons/StarEmpty-Icon.svg";
import StarFullIcon from "../assets/icons/StarFull-Icon.svg";

import { AuthAPI, ProjectsAPI } from "../services/api.ts";

const UserProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { username } = useParams();

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const [user, setUser] = useState<any | null>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isModalClosing, setIsModalClosing] = useState(false);
  const [loading, setLoading] = useState(true);

  const closeModalWithAnimation = () => {
    setIsModalClosing(true);
    setTimeout(() => {
      setSelectedProject(null);
      setIsModalVisible(false);
      setIsModalClosing(false);
    }, 420);
  };

  useEffect(() => {
    async function fetchData() {
      if (!username) return;
      setLoading(true);
      const [userResponse, projectsResponse] = await Promise.all([
        AuthAPI.getUserByUsername(username),
        ProjectsAPI.getPublicProjectsForUser(username),
      ]);

      if (userResponse.ok) {
        setUser(userResponse.data);
      } else {
        setUser(null);
      }

      if (projectsResponse.ok) {
        const projectList = projectsResponse.data?.projects || [];
        setProjects(projectList);
      } else {
        setProjects([]);
      }

      setLoading(false);
    }

    fetchData();
  }, [username]);

  const displayName = user
    ? [user.name, user.family_name].filter(Boolean).join(" ") || user.username
    : loading
    ? "Loading..."
    : "Unknown user";

  const displayUsername = user ? user.username : "";

  const renderStars = (value: number) => {
    return Array.from({ length: 5 }, (_, index) => {
      const filled = index < value;
      const Icon = filled ? StarFullIcon : StarEmptyIcon;
      return <img key={index} src={Icon} alt={filled ? "Filled star" : "Empty star"} />;
    });
  };

  return (
    <div className="profile-page profile-page--public">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onLogout={async () => {
          await AuthAPI.logout();
          navigate("/login");
        }}
        onSelect={(itemId: SidebarItemId) => {
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
        }}
      />

      <Navbar onMenuClick={() => setIsSidebarOpen(true)} />

      <SearchOverlay
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onNavigateToUser={(selectedUsername) => navigate(`/users/${selectedUsername}`)}
      />

      <main className="profile-page__main">
        <section className="profile-page__hero">
          <div className="profile-page__heroImageWrapper">
            <img src={ProfileImage} alt="Profile gradient" />
          </div>

          <div className="profile-page__heroContent">
            <p className="profile-page__heroLabel">I AM</p>

            <h1 className="profile-page__heroName">{displayName}</h1>

            <h2 className="profile-page__heroRole">{displayUsername ? `@${displayUsername}` : ""}</h2>

            <p className="profile-page__heroBio">
              {user
                ? user.bio || "This user has not added a bio yet."
                : loading
                ? "Loading profile..."
                : "User not found."}
            </p>
          </div>
        </section>

        <section className="profile-page__projects">
          <div className="profile-page__projectsGrid">
            {loading ? (
              <p style={{ textAlign: "center", width: "100%", color: "#666" }}>
                Loading profile...
              </p>
            ) : !user ? (
              <p style={{ textAlign: "center", width: "100%", color: "#666" }}>
                User not found.
              </p>
            ) : projects.length > 0 ? (
              projects.map((project, index) => (
                <ProjectCard
                  key={project.project_id || index}
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
                No public projects yet.
              </p>
            )}
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

export default UserProfilePage;