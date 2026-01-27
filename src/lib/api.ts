import { ApiError, ErrorCode } from "./errors";
import type {
  ApiKeyCreate,
  ApiKeyCreated,
  ApiKey,
  AuthTokens,
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectWithStats,
  SubtaskCreate,
  SubtaskUpdate,
  Subtask,
  Task,
  TaskCreate,
  TaskReorder,
  TaskStatusUpdate,
  TaskUpdate,
  User,
  UserCreate,
  UserLogin,
} from "@/types";

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:7655";
const API_V1_PREFIX = "/api/v1";

// ============================================================================
// Storage Keys
// ============================================================================

const TOKEN_KEY = "auth_token";

// ============================================================================
// Token Management
// ============================================================================

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ============================================================================
// Base Fetch Wrapper
// ============================================================================

interface FetchOptions extends RequestInit {
  requiresAuth?: boolean;
  skipRedirectOn401?: boolean;
}

async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const {
    requiresAuth = true,
    skipRedirectOn401 = false,
    headers = {},
    ...rest
  } = options;

  const url = `${API_BASE_URL}${API_V1_PREFIX}${endpoint}`;

  const requestHeaders: Record<string, string> = {
    ...(headers as Record<string, string>),
  };

  // Only set Content-Type if not already provided
  const method = (rest.method || "GET").toUpperCase();
  if (
    !requestHeaders["Content-Type"] &&
    (rest.body || (method !== "GET" && method !== "HEAD"))
  ) {
    requestHeaders["Content-Type"] = "application/json";
  }

  // Add auth token if required
  if (requiresAuth) {
    const token = getToken();
    if (token) {
      requestHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...rest,
    headers: requestHeaders,
  });

  // Handle 401 - only redirect if auth was required and caller didn't opt out
  if (response.status === 401) {
    if (requiresAuth && !skipRedirectOn401) {
      clearToken();
      // Redirect to login page
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    throw new ApiError(ErrorCode.AUTH_REQUIRED);
  }

  // Handle non-2xx responses
  if (!response.ok) {
    let errorCode: ErrorCode = ErrorCode.UNKNOWN;

    try {
      const errorData = await response.json();

      // Handle structured error with code
      if (errorData.detail?.code) {
        errorCode = errorData.detail.code as ErrorCode;
      }
      // Handle FastAPI validation errors (array)
      else if (Array.isArray(errorData.detail)) {
        errorCode = ErrorCode.VALIDATION_ERROR;
      }
      // Fallback: map HTTP status to error code
      else {
        errorCode = mapStatusToErrorCode(response.status);
      }
    } catch {
      // JSON parse failed, use status-based mapping
      errorCode = mapStatusToErrorCode(response.status);
    }

    throw new ApiError(errorCode);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/**
 * Map HTTP status codes to error codes when structured error is not available
 */
function mapStatusToErrorCode(status: number): ErrorCode {
  switch (status) {
    case 401:
      return ErrorCode.AUTH_REQUIRED;
    case 403:
      return ErrorCode.PROJECT_ACCESS_DENIED;
    case 404:
      return ErrorCode.PROJECT_NOT_FOUND;
    case 409:
      return ErrorCode.EMAIL_ALREADY_EXISTS;
    case 422:
      return ErrorCode.VALIDATION_ERROR;
    default:
      return ErrorCode.UNKNOWN;
  }
}

// ============================================================================
// Auth API
// ============================================================================

export const authApi = {
  register: async (data: UserCreate): Promise<User> => {
    return apiFetch<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
      requiresAuth: false,
    });
  },

  login: async (data: UserLogin): Promise<AuthTokens> => {
    const formData = new URLSearchParams();
    formData.append("username", data.email);
    formData.append("password", data.password);

    return apiFetch<AuthTokens>("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
      requiresAuth: false,
      skipRedirectOn401: true,
    });
  },

  me: async (): Promise<User> => {
    return apiFetch<User>("/auth/me", {
      skipRedirectOn401: true,
    });
  },
};

// ============================================================================
// Projects API
// ============================================================================

export const projectsApi = {
  list: async (): Promise<ProjectWithStats[]> => {
    return apiFetch<ProjectWithStats[]>("/projects");
  },

  get: async (id: string): Promise<Project> => {
    return apiFetch<Project>(`/projects/${id}`);
  },

  create: async (data: ProjectCreate): Promise<Project> => {
    return apiFetch<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: ProjectUpdate): Promise<Project> => {
    return apiFetch<Project>(`/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiFetch<void>(`/projects/${id}`, {
      method: "DELETE",
    });
  },
};

// ============================================================================
// Tasks API
// ============================================================================

export const tasksApi = {
  list: async (projectId: string): Promise<Task[]> => {
    return apiFetch<Task[]>(`/projects/${projectId}/tasks`);
  },

  get: async (id: string): Promise<Task> => {
    return apiFetch<Task>(`/tasks/${id}`);
  },

  create: async (projectId: string, data: TaskCreate): Promise<Task> => {
    return apiFetch<Task>(`/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: TaskUpdate): Promise<Task> => {
    return apiFetch<Task>(`/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  updateStatus: async (id: string, data: TaskStatusUpdate): Promise<Task> => {
    return apiFetch<Task>(`/tasks/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  reorder: async (id: string, data: TaskReorder): Promise<Task> => {
    return apiFetch<Task>(`/tasks/${id}/reorder`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiFetch<void>(`/tasks/${id}`, {
      method: "DELETE",
    });
  },
};

// ============================================================================
// Subtasks API
// ============================================================================

export const subtasksApi = {
  list: async (taskId: string): Promise<Subtask[]> => {
    return apiFetch<Subtask[]>(`/tasks/${taskId}/subtasks`);
  },

  create: async (taskId: string, data: SubtaskCreate): Promise<Subtask> => {
    return apiFetch<Subtask>(`/tasks/${taskId}/subtasks`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: SubtaskUpdate): Promise<Subtask> => {
    return apiFetch<Subtask>(`/subtasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiFetch<void>(`/subtasks/${id}`, {
      method: "DELETE",
    });
  },
};

// ============================================================================
// API Keys API
// ============================================================================

export const apiKeysApi = {
  list: async (): Promise<ApiKey[]> => {
    return apiFetch<ApiKey[]>("/api-keys");
  },

  create: async (data: ApiKeyCreate): Promise<ApiKeyCreated> => {
    return apiFetch<ApiKeyCreated>("/api-keys", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiFetch<void>(`/api-keys/${id}`, {
      method: "DELETE",
    });
  },
};
