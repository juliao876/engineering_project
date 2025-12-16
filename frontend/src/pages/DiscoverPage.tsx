import React, { useCallback, useEffect, useMemo, useState } from "react";
import "../styles/DiscoverPage.css";
import "../styles/tokens.css";

import Navbar from "../components/Navbar.tsx";
import Sidebar from "../components/Sidebar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";
import Rating from "../components/Rating.tsx";
import Button from "../components/Button.tsx";

import StarEmptyIcon from "../assets/icons/StarEmpty-Icon.svg";
import StarFullIcon from "../assets/icons/StarFull-Icon.svg";

import { AuthAPI, CollabAPI, FollowAPI, ProjectsAPI } from "../services/api.ts";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider.tsx";
import useSidebarNavigation from "../hooks/useSidebarNavigation.ts";

interface CommentItem {
  id: number;
  project_id: number;
  user_id: number;
  parent_id?: number | null;
  content: string;
  created_at?: string;
  author?: { username?: string; name?: string; family_name?: string };
  replies?: CommentItem[];
}

interface DiscoverProject {
  project_id?: number;
  id?: number;
  title: string;
  description?: string;
  preview_url?: string | null;
  contents?: string;
  figma_link?: string;
  average_rating?: number;
  rating?: number;
  rating_count?: number;
  comments_count?: number;
  username?: string;
  created_at?: string;
}

type FeedTab = "discover" | "followers";

const DiscoverPage: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [activeTab, setActiveTab] = useState<FeedTab>("discover");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const [projects, setProjects] = useState<DiscoverProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<DiscoverProject | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isModalClosing, setIsModalClosing] = useState(false);

  const [comments, setComments] = useState<CommentItem[]>([]);
  const [commentText, setCommentText] = useState("");
  const [replyTexts, setReplyTexts] = useState<Record<number, string>>({});
  const [isCommentsLoading, setIsCommentsLoading] = useState(false);

  const selectedProjectId = useMemo(
    () => selectedProject?.project_id || selectedProject?.id || null,
    [selectedProject],
  );

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

  const handleSidebarSelect = useSidebarNavigation({
    openSearch: () => setIsSearchOpen(true),
  });

  const loadProjects = useCallback(
    async (tab: FeedTab) => {
      setIsLoading(true);
      try {
        const response =
          tab === "discover"
            ? await FollowAPI.getDiscoverFeed()
            : await FollowAPI.getFollowingFeed();

        if (response.ok) {
          const data = response.data?.projects ?? response.data?.feed ?? response.data ?? [];
          const normalized = (Array.isArray(data) ? data : []).map((item) => ({
            ...item,
            preview_url: item.preview_url ?? item.preview ?? item.cover_url ?? null,
          }));

          const shuffled =
            tab === "discover"
              ? [...normalized].sort(() => Math.random() - 0.5)
              : normalized;

          setProjects(shuffled);
        } else {
          setProjects([]);
          addToast({
            message: response.data?.detail || "Could not load projects",
            type: "error",
          });
        }
      } finally {
        setIsLoading(false);
      }
    },
    [addToast],
  );

  useEffect(() => {
    loadProjects(activeTab);
  }, [activeTab, loadProjects]);

  const handleProjectClick = (project: DiscoverProject) => {
    setSelectedProject(project);
    setIsModalVisible(true);
    setIsModalClosing(false);
  };

  const handleAverageUpdate = useCallback((projectId: number, value: number) => {
    setProjects((prev) =>
      prev.map((project) =>
        (project.project_id || project.id) === projectId
          ? { ...project, average_rating: value, rating: value }
          : project,
      ),
    );
    setSelectedProject((prev) =>
      prev && (prev.project_id === projectId || prev.id === projectId)
        ? { ...prev, average_rating: value, rating: value }
        : prev,
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
      const incomingComments = response.data?.comments ?? response.data ?? [];
      setComments(incomingComments);
      const count = Array.isArray(incomingComments) ? incomingComments.length : 0;
      setProjects((prev) =>
        prev.map((project) =>
          (project.project_id || project.id) === selectedProjectId
            ? { ...project, comments_count: count }
            : project,
        ),
      );
      setSelectedProject((prev) =>
        prev && (prev.project_id === selectedProjectId || prev.id === selectedProjectId)
          ? { ...prev, comments_count: count }
          : prev,
      );
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
      setCommentText("");
      fetchComments();
    }
  };

  const handleReplySubmit = async (parentId: number) => {
    if (!replyTexts[parentId]?.trim()) return;
    const response = await CollabAPI.replyToComment(parentId, replyTexts[parentId].trim());
    if (response.ok) {
      setReplyTexts((prev) => ({ ...prev, [parentId]: "" }));
      fetchComments();
    }
  };

  const renderStars = (value: number) =>
    Array.from({ length: 5 }, (_, index) => {
      const filled = index < Math.round(value);
      const Icon = filled ? StarFullIcon : StarEmptyIcon;
      return <img key={index} src={Icon} alt={filled ? "Filled star" : "Empty star"} />;
    });

  return (
    <div className="discover-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        activeItem="home"
        onLogout={handleLogout}
        onSelect={handleSidebarSelect}
      />

      <Navbar onMenuClick={() => setIsSidebarOpen(true)} />

      <SearchOverlay
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onNavigateToUser={(username) => navigate(`/users/${username}`)}
      />

      <main className="discover-page__main">
        <div className="discover-page__hero">
          <div className="discover-page__tabs" role="tablist" aria-label="Project feed tabs">
            <button
              type="button"
              className={`discover-page__tab ${activeTab === "discover" ? "is-active" : ""}`}
              onClick={() => setActiveTab("discover")}
              role="tab"
              aria-selected={activeTab === "discover"}
            >
              Discover
            </button>
            <button
              type="button"
              className={`discover-page__tab ${activeTab === "followers" ? "is-active" : ""}`}
              onClick={() => setActiveTab("followers")}
              role="tab"
              aria-selected={activeTab === "followers"}
            >
              Followers
            </button>
          </div>
        </div>

        <section className="discover-page__grid">
          {isLoading ? (
            <p className="discover-page__empty">Loading projects...</p>
          ) : projects.length > 0 ? (
            projects.map((project, index) => (
              <article
                key={project.project_id || project.id || index}
                className="discover-card"
                onClick={() => handleProjectClick(project)}
              >
                <div className="discover-card__rating">
                  <div className="discover-card__stars">
                    {renderStars(project.average_rating || project.rating || 0)}
                  </div>
                  <span className="discover-card__average">
                    {(project.average_rating || project.rating || 0).toFixed(1)}
                  </span>
                </div>

                <div className="discover-card__media">
                  {project.preview_url ? (
                    <img src={project.preview_url} alt={`${project.title} preview`} />
                  ) : (
                    <div className="discover-card__placeholder" aria-hidden>
                      <span />
                    </div>
                  )}
                </div>

                <div className="discover-card__body">
                  <h3>{project.title}</h3>
                  <p>{project.description || "No description provided."}</p>
                  <div className="discover-card__counts">
                    <span>{project.rating_count ?? 0} ratings</span>
                    <span> · </span>
                    <span>{project.comments_count ?? 0} comments</span>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <p className="discover-page__empty">No projects to display yet.</p>
          )}
        </section>
      </main>

      {isModalVisible && selectedProject && (
        <div
          className={`discover-page__overlay ${isModalClosing ? "is-closing" : ""}`}
          role="dialog"
          aria-modal="true"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              closeModalWithAnimation();
            }
          }}
        >
          <div className={`discover-page__modal ${isModalClosing ? "is-closing" : ""}`}>
            <button
              type="button"
              className="discover-page__close"
              aria-label="Close"
              onClick={closeModalWithAnimation}
            >
              ×
            </button>

            <div className="discover-page__modalGrid">
              <div className="discover-page__modalMedia">
                {selectedProject.preview_url ? (
                  <img
                    src={selectedProject.preview_url}
                    alt={`${selectedProject.title} preview`}
                  />
                ) : (
                  <div className="discover-card__placeholder" aria-hidden>
                    <span />
                  </div>
                )}
              </div>

              <div className="discover-page__modalBody">
                <div className="discover-page__modalHeader">
                  <div>
                    <p className="discover-page__eyebrow">Project details</p>
                    <h3>{selectedProject.title}</h3>
                    <p>{selectedProject.description || "No description provided."}</p>
                  </div>
                  {selectedProject.figma_link && (
                    <a
                      className="button button--medium button--secondary"
                      href={selectedProject.figma_link}
                      target="_blank"
                      rel="noreferrer"
                    >
                      See it in Figma
                    </a>
                  )}
                </div>

                {selectedProjectId && (
                  <div className="discover-page__rating">
                    <Rating
                      projectId={selectedProjectId}
                      initialAverage={selectedProject.average_rating || selectedProject.rating || 0}
                      onAverageChange={(value) => handleAverageUpdate(selectedProjectId, value)}
                    />
                  </div>
                )}

                <div className="discover-page__comments">
                  <div className="discover-page__commentsHeader">
                    <h4>Comments</h4>
                  </div>
                  <form className="discover-page__commentForm" onSubmit={handleCommentSubmit}>
                    <input
                      className="discover-page__commentInput"
                      placeholder="Add a comment"
                      value={commentText}
                      onChange={(event) => setCommentText(event.target.value)}
                    />
                    <Button variant="primary" size="small" type="submit">
                      Send
                    </Button>
                  </form>

                  {isCommentsLoading ? (
                    <p className="discover-page__empty">Loading comments...</p>
                  ) : (
                    <ul className="discover-page__commentList">
                      {comments.length > 0 ? (
                        comments.map((comment) => {
                          const replies = comment.replies || [];
                          return (
                            <li key={comment.id} className="discover-page__commentRow">
                              <div className="discover-page__commentAvatar" aria-hidden>
                                {commentAuthorInitial(comment)}
                              </div>
                              <div className="discover-page__commentBody">
                                <p className="discover-page__commentAuthor">{commentAuthorLabel(comment)}</p>
                                <p className="discover-page__commentText">{comment.content}</p>
                                <div className="discover-page__commentActions">
                                  <button
                                    type="button"
                                    className="discover-page__replyButton"
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
                                    className="discover-page__replyForm"
                                    onSubmit={(event) => {
                                      event.preventDefault();
                                      handleReplySubmit(comment.id);
                                    }}
                                  >
                                    <input
                                      className="discover-page__commentInput"
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
                                  <ul className="discover-page__replyList">
                                    {replies.map((reply) => (
                                      <li key={reply.id} className="discover-page__commentRow is-reply">
                                        <div className="discover-page__commentAvatar" aria-hidden>
                                          {commentAuthorInitial(reply)}
                                        </div>
                                        <div className="discover-page__commentBody">
                                          <p className="discover-page__commentAuthor">{commentAuthorLabel(reply)}</p>
                                          <p className="discover-page__commentText">{reply.content}</p>
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
                        <p className="discover-page__empty">No comments yet.</p>
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

export default DiscoverPage;