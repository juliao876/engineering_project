// ======================
//  UTILITY
// ======================

const withFallback = (value: string | undefined, fallback: string) =>
  value && value.trim().length > 0 ? value : fallback;

// ======================
//  BASE URLS
// ======================

const AUTH_BASE_URL = withFallback(process.env.REACT_APP_AUTH_URL, "http://localhost:6700/api/v1");
const PROJECTS_BASE_URL = withFallback(process.env.REACT_APP_PROJECTS_URL, "http://localhost:6701/api/v1");
const ANALYSIS_BASE_URL = withFallback(process.env.REACT_APP_ANALYSIS_URL, "http://localhost:6703/api/v1");
const FIGMA_BASE_URL = withFallback(process.env.REACT_APP_FIGMA_URL, "http://localhost:6702/api/v1");
const COLLAB_BASE_URL = withFallback(process.env.REACT_APP_COLLAB_URL, "http://localhost:6704/api/v1");
const FOLLOW_BASE_URL = withFallback(process.env.REACT_APP_FOLLOW_URL,"http://localhost:6705/api/v1/DF");

// ======================
//  HEADERS
// ======================

function buildHeaders(body?: any): Record<string, string> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {};

  // Jeśli body jest JSON, ustawiamy Content-Type
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Token autoryzacji
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}

// ======================
//  REQUEST WRAPPER
// ======================

async function request(baseUrl: string, endpoint: string, options: RequestInit = {}) {
  const headers = buildHeaders(options.body);

  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      credentials: "include",
      headers: {
        ...headers,
        ...(options.headers || {}),
      },
    });

    const text = await response.text();
    let data = null;

    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    return {
      ok: response.ok,
      status: response.status,
      data,
    };
  } catch (error: any) {
    return {
      ok: false,
      status: 0,
      data: { detail: error?.message || "Network error" },
    };
  }
}

// ======================
//  AUTH API
// ======================

export const AuthAPI = {
  register: (payload: any) =>
    request(AUTH_BASE_URL, "/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (payload: any) =>
    request(AUTH_BASE_URL, "/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  me: () =>
    request(AUTH_BASE_URL, "/auth/me", {
      method: "GET",
    }),

  logout: () =>
    request(AUTH_BASE_URL, "/auth/logout", {
      method: "POST",
    }),

  updateMe: (payload: any) =>
    request(AUTH_BASE_URL, "/auth/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request(AUTH_BASE_URL, "/auth/me/avatar", {
      method: "POST",
      body: formData,
    });
  },

  searchUsers: (query: string) =>
    request(
      AUTH_BASE_URL,
      `/auth/search?query=${encodeURIComponent(query)}`,
      { method: "GET" }
    ),

  getUserByUsername: (username: string) =>
    request(AUTH_BASE_URL, `/auth/user/${encodeURIComponent(username)}`, {
      method: "GET",
    }),
};

// ======================
//  PROJECTS API
// ======================

export const ProjectsAPI = {
  getMyProjects: () =>
    request(PROJECTS_BASE_URL, "/project/my", {
      method: "GET",
    }),

  deleteProject: (projectId: number) =>
    request(PROJECTS_BASE_URL, `/project/delete_project/${projectId}`, {
      method: "DELETE",
    }),

  updateProject: (projectId: number, payload: any) =>
    request(PROJECTS_BASE_URL, `/project/update_project/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  createProject: (form: FormData) =>
    request(PROJECTS_BASE_URL, "/project/create_project", {
      method: "POST",
      body: form, // NIE ustawiamy Content-Type
    }),

  importFigma: (payload: { file_url: string }) =>
    request(FIGMA_BASE_URL, "/figma/import", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getPublicProjectsForUser: (username: string) =>
    request(PROJECTS_BASE_URL, `/project/public/${username}`, {
      method: "GET",
    }),

  getProjectDetails: (projectId: number) =>
    request(PROJECTS_BASE_URL, `/project/details/${projectId}`, {
      method: "GET",
    }),
};

// ======================
//  FIGMA API
// ======================

export const FigmaAPI = {
  buildAuthUrl: (credentials?: { clientId?: string; clientSecret?: string; redirectUri?: string }) =>
    request(FIGMA_BASE_URL, "/figma/auth-url", {
      method: "GET",
      headers: {
        ...(credentials?.clientId ? { "x-figma-client-id": credentials.clientId } : {}),
        ...(credentials?.clientSecret ? { "x-figma-client-secret": credentials.clientSecret } : {}),
        ...(credentials?.redirectUri ? { "x-figma-redirect-uri": credentials.redirectUri } : {}),
      },
    }),

  connect: (payload: {
    code: string;
    state?: string | null;
    clientId?: string;
    clientSecret?: string;
    redirectUri?: string;
  }) =>
    request(FIGMA_BASE_URL, "/figma/connect", {
      method: "POST",
      body: JSON.stringify({
        code: payload.code,
        state: payload.state,
        client_id: payload.clientId,
        client_secret: payload.clientSecret,
        redirect_uri: payload.redirectUri,
      }),
    }),

  importFile: (payload: { file_url: string }) =>
    request(FIGMA_BASE_URL, "/figma/import", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

// ======================
//  ANALYSIS API
// ======================

export const AnalysisAPI = {
  runAnalysis: (projectId: number, payload: { device: "desktop" | "mobile" }) =>
    request(ANALYSIS_BASE_URL, `/analysis/${projectId}`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getAnalysis: (projectId: number) =>
    request(ANALYSIS_BASE_URL, `/analysis/${projectId}`, { method: "GET" }),
};

// ======================
//  COLLAB API
// ======================

export const CollabAPI = {
  rateProject: (projectId: number, value: number) =>
    request(COLLAB_BASE_URL, `/collab/projects/${projectId}/rating`, {
      method: "POST",
      body: JSON.stringify({ value }),
    }),

  getProjectRating: (projectId: number) =>
    request(COLLAB_BASE_URL, `/collab/projects/${projectId}/rating`, {
      method: "GET",
    }),

  getProjectComments: (projectId: number) =>
    request(COLLAB_BASE_URL, `/collab/projects/${projectId}/comments`, {
      method: "GET",
    }),

  addProjectComment: (projectId: number, content: string) =>
    request(COLLAB_BASE_URL, `/collab/projects/${projectId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  replyToComment: (commentId: number, content: string) =>
    request(COLLAB_BASE_URL, `/collab/comments/${commentId}/reply`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
};
// ======================
//  FOLLOW API
// ======================

export const FollowAPI = {
  toggleFollow: (followingId: number) =>
    request(FOLLOW_BASE_URL, "/users/follow", {
      method: "POST",
      body: JSON.stringify({ following_id: followingId }),
    }),

  getStatus: (username: string) =>
    request(FOLLOW_BASE_URL, `/users/${username}/follow-status`, {
      method: "GET",
    }),

  getDiscoverFeed: () =>
    request(FOLLOW_BASE_URL, "/discover", {
      method: "GET",
    }),

  getFollowingFeed: () =>
    request(FOLLOW_BASE_URL, "/feed/following", {
      method: "GET",
    }),
}


export default request;