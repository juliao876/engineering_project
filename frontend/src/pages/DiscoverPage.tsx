import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "../styles/DiscoverPage.css";
import "../styles/tokens.css";

import Navbar from "../components/Navbar.tsx";
import Sidebar from "../components/Sidebar.tsx";
import SearchOverlay from "../components/SearchOverlay.tsx";
import Rating from "../components/Rating.tsx";
import Button from "../components/Button.tsx";
import ProjectCard from "../components/ProjectCard.tsx";

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
  user_id?: number;
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
  avatar_url?: string;
  profile_photo?: string;
  profile_picture?: string;
  user_photo?: string;
  name?: string;
  family_name?: string;
  role?: string;
  job_title?: string;
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

  const fetchedAuthorProjectsRef = useRef<Set<number>>(new Set());

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
      fetchedAuthorProjectsRef.current.clear();
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

  const projectAuthorAvatar = useCallback(
    (project?: DiscoverProject | null) =>
      project?.avatar_url || project?.profile_photo || project?.profile_picture || project?.user_photo,
    [],
  );

  const fetchProjectAuthor = useCallback(
    async (projectId?: number | null) => {
      if (!projectId || fetchedAuthorProjectsRef.current.has(projectId)) return;

      fetchedAuthorProjectsRef.current.add(projectId);

      const detailsResponse = await ProjectsAPI.getProjectDetails(projectId);
      if (!detailsResponse.ok) return;

      const projectDetails = detailsResponse.data?.project ?? detailsResponse.data;
      const ownerId: number | undefined = projectDetails?.user_id;

      const userResponse = ownerId ? await AuthAPI.getUserById(ownerId) : null;
      const userProfile = userResponse?.ok ? userResponse.data?.user ?? userResponse.data : null;

      if (projectDetails || userProfile) {
        setProjects((prev) =>
          prev.map((item) => {
            const itemId = item.project_id || item.id;
            if (itemId !== projectId) return item;

            return {
              ...item,
              user_id: item.user_id ?? ownerId,
              username: item.username ?? userProfile?.username,
              name: item.name ?? userProfile?.name,
              family_name: item.family_name ?? userProfile?.family_name,
              role: item.role ?? userProfile?.role,
              job_title: item.job_title ?? userProfile?.role,
            };
          }),
        );

        setSelectedProject((prev) => {
          if (!prev || (prev.project_id || prev.id) !== projectId) return prev;

          return {
            ...prev,
            user_id: prev.user_id ?? ownerId,
            username: prev.username ?? userProfile?.username,
            name: prev.name ?? userProfile?.name,
            family_name: prev.family_name ?? userProfile?.family_name,
            role: prev.role ?? userProfile?.role,
            job_title: prev.job_title ?? userProfile?.role,
          };
        });
      }
    },
    [],
  );

  useEffect(() => {
    projects.forEach((project) => {
      const projectId = project.project_id || project.id;
      const hasAuthor = project.username || project.name || project.family_name;
      if (!hasAuthor) {
        fetchProjectAuthor(projectId);
      }
    });
  }, [fetchProjectAuthor, projects]);

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
            projects.map((project, index) => {
              const projectId = project.project_id || project.id || index;
              const avatarUrl = projectAuthorAvatar(project);
              const authorName =
                [project.name, project.family_name].filter(Boolean).join(" ") || project.username || "Unknown";
              const authorSubtitle = project.role || project.job_title || (project.username ? `@${project.username}` : "");

              return (
                <ProjectCard
                  key={projectId}
                  projectId={projectId}
                  title={project.title}
                  description={project.description || "No description provided."}
                  rating={project.average_rating || project.rating || 0}
                  commentsCount={project.comments_count || 0}
                  figmaUrl={project.figma_link}
                  previewUrl={project.preview_url}
                  contentType={project.contents}
                  onPreviewClick={() => handleProjectClick(project)}
                  authorUsername={authorName}
                  authorAvatarUrl={avatarUrl}
                  authorSubtitle={authorSubtitle}
                  onAuthorClick={() => project.username && navigate(`/users/${project.username}`)}
                  ratingCount={project.rating_count}
                />
              );
            })
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
                  <div className="discover-page__modalAuthor">
                    <button
                      type="button"
                      className="project-card__author discover-page__modalAuthorButton"
                      onClick={() => selectedProject.username && navigate(`/users/${selectedProject.username}`)}
                      disabled={!selectedProject.username}
                    >
                      {projectAuthorAvatar(selectedProject) ? (
                        <img
                          src={projectAuthorAvatar(selectedProject) as string}
                          alt={selectedProject.username ? `${selectedProject.username}'s avatar` : "Author avatar"}
                          className="project-card__authorAvatar"
                        />
                      ) : (
                        <span className="project-card__authorAvatar">
                          {selectedProject.username?.charAt(0).toUpperCase() || "?"}
                        </span>
                      )}
                      <span className="discover-page__modalAuthorText">
                        <span className="project-card__authorName">
                          {[selectedProject.name, selectedProject.family_name]
                            .filter(Boolean)
                            .join(" ") || selectedProject.username || "Unknown author"}
                        </span>
                        <span className="project-card__authorSubtitle">
                          {selectedProject.role || selectedProject.job_title ||
                            (selectedProject.username ? `@${selectedProject.username}` : "Author")}
                        </span>
                      </span>
                    </button>
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

                <div className="discover-page__modalHeading">
                  <p className="discover-page__eyebrow">Project details</p>
                  <h3>{selectedProject.title}</h3>
                  <p>{selectedProject.description || "No description provided."}</p>
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