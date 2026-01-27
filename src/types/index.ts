// Core domain types matching backend schemas

// ============================================================================
// User Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserUpdate {
  full_name?: string;
}

// ============================================================================
// Project Types
// ============================================================================

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
}

export interface ProjectWithStats extends Project {
  task_count: number;
  done_count: number;
}

// ============================================================================
// Task Types
// ============================================================================

export type TaskStatus = "backlog" | "todo" | "in_progress" | "done";

export type TaskPriority = "low" | "medium" | "high" | "urgent";

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  position: number;
  created_at: string;
  updated_at: string;
  subtasks?: Subtask[];
}

export interface TaskCreate {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
}

export interface TaskUpdate {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  position?: number;
}

export interface TaskStatusUpdate {
  status: TaskStatus;
}

export interface TaskReorder {
  position: number;
  status?: TaskStatus;
}

// ============================================================================
// Subtask Types
// ============================================================================

export interface Subtask {
  id: string;
  task_id: string;
  title: string;
  is_completed: boolean;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface SubtaskCreate {
  title: string;
}

export interface SubtaskUpdate {
  title?: string;
  is_completed?: boolean;
  position?: number;
}

// ============================================================================
// API Key Types
// ============================================================================

export interface ApiKey {
  id: string;
  user_id: string;
  name: string;
  key_prefix: string;
  key_suffix: string | null;
  last_used_at: string | null;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface ApiKeyCreate {
  name: string;
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  key: string; // Full key only shown once
  key_prefix: string;
  key_suffix: string;
  created_at: string;
}

// ============================================================================
// Auth Types
// ============================================================================

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiError {
  detail: string | Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ============================================================================
// Helper Types
// ============================================================================

export type LoadingState = "idle" | "loading" | "success" | "error";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}
