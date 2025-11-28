const BASE_URL = "http://localhost:6700/api/v1";

function getHeaders(isJSON = true) {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {};

  if (isJSON) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  return headers;
}

async function request(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      ...getHeaders(options.body !== undefined),
      ...options.headers,
    },
  });

  const text = await response.text();
  let data = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch (e) {
    data = text;
  }

  return {
    ok: response.ok,
    status: response.status,
    data,
  };
}
export const AuthAPI = {
  register: (payload: any) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (payload: any) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  me: () =>
    request("/auth/me", {
      method: "GET",
    }),

  logout: () =>
    request("/auth/logout", {
      method: "POST",
    }),
};
export const ProjectsAPI = {
  getMyProjects: () =>
    request("/auth/projects", {
      method: "GET",
    }),

  getUserByUsername: (username: string) =>
    request(`/auth/user/${username}`, {
      method: "GET",
    }),
};

export default request;