/**
 * Error codes returned by the API
 */
export const ErrorCode = {
  // Auth
  AUTH_REQUIRED: "AUTH_REQUIRED",
  INVALID_CREDENTIALS: "INVALID_CREDENTIALS",
  INVALID_TOKEN: "INVALID_TOKEN",
  TOKEN_EXPIRED: "TOKEN_EXPIRED",
  USER_INACTIVE: "USER_INACTIVE",

  // Registration
  EMAIL_ALREADY_EXISTS: "EMAIL_ALREADY_EXISTS",

  // API Keys
  API_KEY_REQUIRED: "API_KEY_REQUIRED",
  API_KEY_INVALID_FORMAT: "API_KEY_INVALID_FORMAT",
  API_KEY_INVALID: "API_KEY_INVALID",
  API_KEY_EXPIRED: "API_KEY_EXPIRED",
  API_KEY_NOT_FOUND: "API_KEY_NOT_FOUND",

  // Projects
  PROJECT_NOT_FOUND: "PROJECT_NOT_FOUND",
  PROJECT_ACCESS_DENIED: "PROJECT_ACCESS_DENIED",

  // Tasks
  TASK_NOT_FOUND: "TASK_NOT_FOUND",
  TASK_ACCESS_DENIED: "TASK_ACCESS_DENIED",

  // Subtasks
  SUBTASK_NOT_FOUND: "SUBTASK_NOT_FOUND",
  SUBTASK_ACCESS_DENIED: "SUBTASK_ACCESS_DENIED",

  // Invitations
  INVITATION_EXPIRED: "INVITATION_EXPIRED",
  INVITATION_NOT_FOUND: "INVITATION_NOT_FOUND",
  INVITATION_ALREADY_SENT: "INVITATION_ALREADY_SENT",
  EMAIL_MISMATCH: "EMAIL_MISMATCH",
  ALREADY_MEMBER: "ALREADY_MEMBER",
  LAST_OWNER: "LAST_OWNER",
  CANNOT_REMOVE_CREATOR: "CANNOT_REMOVE_CREATOR",

  // Validation
  VALIDATION_ERROR: "VALIDATION_ERROR",

  // Client-side
  REGISTRATION_SUCCESS_LOGIN_FAILED: "REGISTRATION_SUCCESS_LOGIN_FAILED",
  UNKNOWN: "UNKNOWN",
} as const;

export type ErrorCode = typeof ErrorCode[keyof typeof ErrorCode];

/**
 * User-friendly error messages mapped by code
 * These messages are clear, actionable, and guide the user on what to do next
 */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  // Auth - clear, actionable messages
  [ErrorCode.AUTH_REQUIRED]: "Please log in to continue.",
  [ErrorCode.INVALID_CREDENTIALS]:
    "Incorrect email or password. Please check your details and try again.",
  [ErrorCode.INVALID_TOKEN]: "Your session has expired. Please log in again.",
  [ErrorCode.TOKEN_EXPIRED]: "Your session has expired. Please log in again.",
  [ErrorCode.USER_INACTIVE]:
    "Your account is inactive. Please contact support.",

  // Registration
  [ErrorCode.EMAIL_ALREADY_EXISTS]:
    "An account with this email already exists. Please log in instead.",

  // API Keys
  [ErrorCode.API_KEY_REQUIRED]: "API key is required for this request.",
  [ErrorCode.API_KEY_INVALID_FORMAT]:
    "Invalid API key format. Keys should start with 'ak_'.",
  [ErrorCode.API_KEY_INVALID]:
    "Invalid API key. Please check your key and try again.",
  [ErrorCode.API_KEY_EXPIRED]:
    "Your API key has expired. Please generate a new one.",
  [ErrorCode.API_KEY_NOT_FOUND]: "API key not found or already revoked.",

  // Projects
  [ErrorCode.PROJECT_NOT_FOUND]:
    "Project not found. It may have been deleted.",
  [ErrorCode.PROJECT_ACCESS_DENIED]: "You don't have access to this project.",

  // Tasks
  [ErrorCode.TASK_NOT_FOUND]: "Task not found. It may have been deleted.",
  [ErrorCode.TASK_ACCESS_DENIED]: "You don't have access to this task.",

  // Subtasks
  [ErrorCode.SUBTASK_NOT_FOUND]:
    "Subtask not found. It may have been deleted.",
  [ErrorCode.SUBTASK_ACCESS_DENIED]: "You don't have access to this subtask.",

  // Invitations
  [ErrorCode.INVITATION_EXPIRED]:
    "This invitation has expired. Please contact the project owner for a new invitation.",
  [ErrorCode.INVITATION_NOT_FOUND]:
    "Invitation not found or already accepted.",
  [ErrorCode.INVITATION_ALREADY_SENT]:
    "An invitation has already been sent to this email address.",
  [ErrorCode.EMAIL_MISMATCH]:
    "This invitation is for a different email address. Please log in with the correct account.",
  [ErrorCode.ALREADY_MEMBER]:
    "You are already a member of this project.",
  [ErrorCode.LAST_OWNER]:
    "Cannot demote the last owner. Promote another member to owner first.",
  [ErrorCode.CANNOT_REMOVE_CREATOR]:
    "Cannot remove the original project creator.",

  // Validation
  [ErrorCode.VALIDATION_ERROR]: "Please check your input and try again.",

  // Client-side
  [ErrorCode.REGISTRATION_SUCCESS_LOGIN_FAILED]:
    "Account created! Please log in with your new credentials.",
  [ErrorCode.UNKNOWN]: "Something went wrong. Please try again.",
};

/**
 * Custom API error with code
 */
export class ApiError extends Error {
  code: ErrorCode;

  constructor(code: ErrorCode, message?: string) {
    super(
      message || ERROR_MESSAGES[code] || ERROR_MESSAGES[ErrorCode.UNKNOWN]
    );
    this.code = code;
    this.name = "ApiError";
  }

  /** Get user-friendly message for this error */
  get userMessage(): string {
    return ERROR_MESSAGES[this.code] || ERROR_MESSAGES[ErrorCode.UNKNOWN];
  }
}

/**
 * Get user-friendly message for an error code
 */
export function getErrorMessage(code: ErrorCode | string): string {
  return (
    ERROR_MESSAGES[code as ErrorCode] || ERROR_MESSAGES[ErrorCode.UNKNOWN]
  );
}
