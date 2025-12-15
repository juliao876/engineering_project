import React, { useCallback, useEffect, useState } from "react";
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
import Rating from "../components/Rating.tsx";
import { useToast } from "../components/ToastProvider.tsx";

import { AuthAPI, CollabAPI, ProjectsAPI } from "../services/api.ts";
import { useNavigate } from "react-router-dom";

type CommentItem = {
  id: number;
  project_id: number;
  user_id: number;
  parent_id?: number | null;
  content: string;
  created_at?: string;
  author?: { username?: string; name?: string; family_name?: string };
  replies?: CommentItem[];
};

const MyProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const [user, setUser] = useState<any>(null);

  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isModalClosing, setIsModalClosing] = useState(false);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [commentText, setCommentText] = useState("");
  const [replyTexts, setReplyTexts] = useState<Record<number, string>>({});
  const [isCommentsLoading, setIsCommentsLoading] = useState(false);

  const closeModalWithAnimation = () => {
    setIsModalClosing(true);
    setTimeout(() => {
      setIsModalVisible(false);
      setSelectedProject(null);
      setComments([]);
      setCommentText("");
      setReplyTexts({});
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

  const projectIdFor = useCallback((project: any) => project?.project_id || project?.id, []);

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

  const handleToggleVisibility = async (project: any) => {
    const id = projectIdFor(project);
    if (!id) return;
    const nextVisibility = !project.is_public;
    const response = await ProjectsAPI.updateProject(id, { is_public: nextVisibility });
    if (response.ok) {
      setProjects((prev) =>
        prev.map((p) =>
          projectIdFor(p) === id ? { ...p, is_public: nextVisibility } : p,
        ),
      );
      setSelectedProject((prev) =>
        prev && projectIdFor(prev) === id ? { ...prev, is_public: nextVisibility } : prev,
      );
      addToast({
        message: nextVisibility ? "Project is now public" : "Project is now private",
        type: "success",
      });
    } else {
      addToast({
        message: response.data?.detail || "Could not update visibility",
        type: "error",
      });
    }
  };

  const handleDeleteProject = async (projectId?: number) => {
    if (!projectId) return;
    const response = await ProjectsAPI.deleteProject(projectId);
    if (response.ok) {
      setProjects((prev) => prev.filter((p) => projectIdFor(p) !== projectId));
      if (selectedProjectId === projectId) {
        closeModalWithAnimation();
      }
      addToast({ message: "Project deleted", type: "success" });
    } else {
      addToast({
        message: response.data?.detail || "Could not delete project",
        type: "error",
      });
    }
  };

  const displayName = user
    ? [user.name, user.family_name].filter(Boolean).join(" ") || user.username
    : "Loading...";

  const displayUsername = user ? user.username : "";
  const avatarSrc = user?.avatar_url || ProfileImage;

  // const renderStars = (value: number) => {
  //   return Array.from({ length: 5 }, (_, index) => {
  //     const filled = index < value;
  //     const Icon = filled ? StarFullIcon : StarEmptyIcon;
  //     return <img key={index} src={Icon} alt={filled ? "Filled star" : "Empty star"} />;
  //   });
  // };
    const selectedProjectId = selectedProject ? selectedProject.project_id || selectedProject.id : null;

  const handleAverageUpdate = useCallback((projectId: number, value: number) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.project_id === projectId || project.id === projectId
          ? { ...project, average_rating: value, rating: value }
          : project,
      ),
    );
    setSelectedProject((prev) =>
      prev ? { ...prev, average_rating: value, rating: value } : prev,
    );
  }, []);

  const commentAuthorLabel = useCallback((comment: CommentItem) => {
    const username = comment.author?.username;
    const fullName = [comment.author?.name, comment.author?.family_name]
      .filter(Boolean)
      .join(" ");
    return username || fullName || "Anonymous";
  }, []);

  const commentAuthorInitial = useCallback(
    (comment: CommentItem) => (commentAuthorLabel(comment).charAt(0) || "?").toUpperCase(),
    [commentAuthorLabel],
  );

  const fetchComments = useCallback(async () => {
    if (!selectedProjectId) return;
    setIsCommentsLoading(true);
    const response = await CollabAPI.getProjectComments(selectedProjectId);
    if (response.ok) {
      setComments(response.data?.comments || response.data || []);
    } else {
      setComments([]);
    }
    setIsCommentsLoading(false);
  }, [selectedProjectId]);

  useEffect(() => {
    if (isModalVisible && selectedProjectId) {
      fetchComments();
    }
  }, [fetchComments, isModalVisible, selectedProjectId]);

  const handleCommentSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !commentText.trim()) return;

    const response = await CollabAPI.addProjectComment(selectedProjectId, commentText.trim());
    if (response.ok) {
      const newComment: CommentItem = response.data?.comment || response.data;
      setComments((prev) => [newComment, ...(prev || [])]);
      setCommentText("");
    }
  };

  const insertReply = (list: CommentItem[], parentId: number, reply: CommentItem): CommentItem[] =>
    list.map((item) => {
      if (item.id === parentId) {
        return { ...item, replies: [reply, ...(item.replies || [])] };
      }
      if (item.replies && item.replies.length > 0) {
        return { ...item, replies: insertReply(item.replies, parentId, reply) };
      }
      return item;
    });

  const handleReplySubmit = async (commentId: number) => {
    const replyValue = replyTexts[commentId];
    if (!replyValue || !replyValue.trim()) return;

    const response = await CollabAPI.replyToComment(commentId, replyValue.trim());
    if (response.ok) {
      const reply: CommentItem = response.data?.reply || response.data;
      setComments((prev) => insertReply(prev, commentId, reply));
      setReplyTexts((prev) => ({ ...prev, [commentId]: "" }));
    }
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
            <div
              className="profile-page__heroMaskedImage"
              style={{ backgroundImage: `url(${avatarSrc})` }}
              aria-label="Profile avatar"
            />
          </div>

          <div className="profile-page__heroContent">
            <p className="profile-page__heroLabel">I AM</p>

            <h1 className="profile-page__heroName">{displayName}</h1>

            <h2 className="profile-page__heroRole">{displayUsername}</h2>

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
                  projectId={project.project_id || project.id || index}
                  title={project.title}
                  description={project.description || ""}
                  rating={project.average_rating || project.rating || 0}
                  commentsCount={project.comments || 0}
                  figmaUrl={project.figma_link}
                  previewUrl={project.preview_url}
                  contentType={project.contents}
                  isPublic={project.is_public}
                  onToggleVisibility={() => handleToggleVisibility(project)}
                  onDelete={() => handleDeleteProject(projectIdFor(project))}
                  onPreviewClick={() => {
                    setSelectedProject(project);
                    setIsModalVisible(true);
                    setIsModalClosing(false);
                  }}
                  onAnalyzeClick={() =>
                    navigate(`/analysis/${project.project_id || project.id || index}`)
                  }
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
                      className="profile-page__figmaAction button button--medium button--secondary"
                      href={selectedProject.figma_link}
                      target="_blank"
                      rel="noreferrer"
                    >
                      See it in Figma
                    </a>
                  )}
                </div>
                {selectedProject && selectedProjectId && (
                  <div className="profile-page__figmaRating">
                    <Rating
                      projectId={selectedProjectId}
                      initialAverage={selectedProject.average_rating || selectedProject.rating || 0}
                      onAverageChange={(value) =>
                        handleAverageUpdate(selectedProjectId, value)
                      }
                    />
                  </div>
                )}

                {/* <div className="profile-page__figmaRating">{renderStars(selectedProject.rating || 0)}</div> */}

                <div className="profile-page__commentsBlock">
                  <div className="profile-page__commentsHeader">
                    <h4>Comments</h4>
                  </div>
                  <form className="profile-page__commentForm" onSubmit={handleCommentSubmit}>
                    <input
                      className="profile-page__commentInput"
                      placeholder="Add a comment"
                      value={commentText}
                      onChange={(event) => setCommentText(event.target.value)}
                    />
                    <Button variant="primary" size="small" type="submit">
                      Send
                    </Button>
                  </form>

                  {isCommentsLoading ? (
                    <p className="profile-page__commentEmpty">Loading comments...</p>
                  ) : (
                    <ul className="profile-page__commentsList">
                      {comments.length > 0 ? (
                        comments.map((comment) => {
                          const replies = comment.replies || [];
                          return (
                            <li key={comment.id} className="profile-page__commentRow">
                              <div className="profile-page__commentAvatar" aria-hidden>
                                {commentAuthorInitial(comment)}
                              </div>
                              <div className="profile-page__commentBody">
                                <p className="profile-page__commentAuthor">{commentAuthorLabel(comment)}</p>
                                <p className="profile-page__commentText">{comment.content}</p>
                                <div className="profile-page__commentActions">
                                  <button
                                    type="button"
                                    className="profile-page__replyButton"
                                    onClick={() =>
                                      setReplyTexts((prev) => ({
                                        ...prev,
                                        [comment.id]: prev[comment.id] ?? "",
                                      }))
                                    }
                                  >
                                    Reply
                                  </button>
                                </div>
                                {replyTexts[comment.id] !== undefined && (
                                  <form
                                    className="profile-page__replyForm"
                                    onSubmit={(event) => {
                                      event.preventDefault();
                                      handleReplySubmit(comment.id);
                                    }}
                                  >
                                    <input
                                      className="profile-page__commentInput"
                                      placeholder="Write a reply"
                                      value={replyTexts[comment.id] || ""}
                                      onChange={(event) =>
                                        setReplyTexts((prev) => ({
                                          ...prev,
                                          [comment.id]: event.target.value,
                                        }))
                                      }
                                    />
                                    <Button variant="secondary" size="small" type="submit">
                                      Reply
                                    </Button>
                                  </form>
                                )}

                                {replies.length > 0 && (
                                  <ul className="profile-page__replyList">
                                    {replies.map((reply) => (
                                      <li key={reply.id} className="profile-page__commentRow">
                                        <div className="profile-page__commentAvatar" aria-hidden>
                                          {commentAuthorInitial(reply)}
                                        </div>
                                        <div className="profile-page__commentBody">
                                          <p className="profile-page__commentAuthor">{commentAuthorLabel(reply)}</p>
                                          <p className="profile-page__commentText">{reply.content}</p>
                                        </div>
                                      </li>
                                    ))}
                                  </ul>
                                )}
                              </div>
                            </li>
                          );
                        })
                      ) : (
                        <li className="profile-page__commentEmpty">No comments yet.</li>
                      )}
                    </ul>
                  )}
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