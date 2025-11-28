import React, { useEffect, useState } from "react";
import "../styles/MyProfilePage.css";
import "../styles/tokens.css";

import Logo from "../assets/icons/Logo.svg";
import ProfileImage from "../assets/images/Profile.png";

import Sidebar from "../components/Sidebar.tsx";
import ProjectCard from "../components/ProjectCard.tsx";
import Button from "../components/Button.tsx";

import { AuthAPI, ProjectsAPI } from "../services/api.ts";
import { useNavigate } from "react-router-dom";

const MyProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const [user, setUser] = useState<any>(null);

  const [projects, setProjects] = useState<any[]>([]);

  const handleLogout = async () => {
    await AuthAPI.logout();
    localStorage.removeItem("token");
    navigate("/login");
  };

  useEffect(() => {
    async function loadData() {
      const me = await AuthAPI.me();

      if (me.ok) {
        setUser(me.data);
      } else {
        console.log("Failed to load user profile", me.data);
        if (me.status === 401) navigate("/login");
      }
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

  return (
    <div className="profile-page">
      {/* SIDEBAR */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        activeItem="profile"
        onLogout={handleLogout}
      />

      {/* HEADER */}
      <header className="profile-page__header">
        <div className="profile-page__logo">
          <img src={Logo} alt="uinside logo" />
        </div>

        <button
          type="button"
          className="profile-page__menuButton"
          aria-label="Open navigation"
          onClick={() => setIsSidebarOpen(true)}
        >
          <span />
          <span />
          <span />
        </button>
      </header>

      {/* MAIN */}
      <main className="profile-page__main">
        {/* HERO */}
        <section className="profile-page__hero">
          <div className="profile-page__heroImageWrapper">
            <div
              className="profile-page__heroMaskedImage"
              style={{
                backgroundImage: `url(${user?.avatar_url || ProfileImage})`,
              }}
            />
          </div>

          <div className="profile-page__heroContent">
            <p className="profile-page__heroLabel">I AM</p>

            <h1 className="profile-page__heroName">
              {user ? user.username : "Loading..."}
            </h1>

            <h2 className="profile-page__heroRole">
              {user ? user.role || "Designer" : ""}
            </h2>

            <p className="profile-page__heroBio">
              {user
                ? user.bio ||
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
                  description={project.description}
                  rating={project.rating || 0}
                  commentsCount={project.comments || 0}
                  figmaUrl={project.figma_url}
                />
              ))
            ) : (
              <p style={{ textAlign: "center", width: "100%", color: "#666" }}>
                No projects yet.
              </p>
            )}
          </div>

          <div className="profile-page__createWrapper">
            <Button variant="secondary" size="medium">
              Create new Project
            </Button>
          </div>
        </section>
      </main>

      <div className="profile-page__bottomGradient" />
    </div>
  );
};

export default MyProfilePage;