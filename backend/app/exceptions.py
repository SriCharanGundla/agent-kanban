"""Structured Application Exceptions"""

from enum import Enum
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Application error codes"""

    # Authentication & Authorization
    AUTH_REQUIRED = "AUTH_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    USER_INACTIVE = "USER_INACTIVE"

    # Registration
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"

    # API Keys
    API_KEY_REQUIRED = "API_KEY_REQUIRED"
    API_KEY_INVALID_FORMAT = "API_KEY_INVALID_FORMAT"
    API_KEY_INVALID = "API_KEY_INVALID"
    API_KEY_EXPIRED = "API_KEY_EXPIRED"
    API_KEY_NOT_FOUND = "API_KEY_NOT_FOUND"

    # Projects
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_ACCESS_DENIED = "PROJECT_ACCESS_DENIED"

    # Tasks
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ACCESS_DENIED = "TASK_ACCESS_DENIED"

    # Subtasks
    SUBTASK_NOT_FOUND = "SUBTASK_NOT_FOUND"
    SUBTASK_ACCESS_DENIED = "SUBTASK_ACCESS_DENIED"

    # Invitations & Members
    INVITATION_EXPIRED = "INVITATION_EXPIRED"
    INVITATION_NOT_FOUND = "INVITATION_NOT_FOUND"
    INVITATION_ALREADY_SENT = "INVITATION_ALREADY_SENT"
    EMAIL_MISMATCH = "EMAIL_MISMATCH"
    ALREADY_MEMBER = "ALREADY_MEMBER"
    LAST_OWNER = "LAST_OWNER"
    CANNOT_REMOVE_CREATOR = "CANNOT_REMOVE_CREATOR"
    MEMBER_NOT_FOUND = "MEMBER_NOT_FOUND"

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"


class AppException(HTTPException):
    """HTTPException with structured error code"""

    def __init__(
        self,
        status_code: int,
        code: ErrorCode,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={"code": code.value},
            headers=headers,
        )


# Convenience factory functions for common errors
def auth_required() -> AppException:
    """Authentication is required"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.AUTH_REQUIRED,
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_credentials() -> AppException:
    """Invalid email or password"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.INVALID_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_token() -> AppException:
    """Invalid or expired JWT token"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.INVALID_TOKEN,
        headers={"WWW-Authenticate": "Bearer"},
    )


def user_inactive() -> AppException:
    """User account is inactive or deleted"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.USER_INACTIVE,
        headers={"WWW-Authenticate": "Bearer"},
    )


def email_already_exists() -> AppException:
    """Email is already registered"""
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code=ErrorCode.EMAIL_ALREADY_EXISTS,
    )


def api_key_required() -> AppException:
    """API key is required"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.API_KEY_REQUIRED,
        headers={"WWW-Authenticate": 'ApiKey realm="API Key"'},
    )


def api_key_invalid_format() -> AppException:
    """API key format is invalid"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.API_KEY_INVALID_FORMAT,
    )


def api_key_invalid() -> AppException:
    """API key is invalid or inactive"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.API_KEY_INVALID,
    )


def api_key_expired() -> AppException:
    """API key has expired"""
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.API_KEY_EXPIRED,
    )


def api_key_not_found() -> AppException:
    """API key not found"""
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.API_KEY_NOT_FOUND,
    )


def project_not_found() -> AppException:
    """Project not found"""
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.PROJECT_NOT_FOUND,
    )


def project_access_denied() -> AppException:
    """User doesn't have access to this project"""
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ErrorCode.PROJECT_ACCESS_DENIED,
    )


def task_not_found() -> AppException:
    """Task not found"""
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.TASK_NOT_FOUND,
    )


def task_access_denied() -> AppException:
    """User doesn't have access to this task"""
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ErrorCode.TASK_ACCESS_DENIED,
    )


def subtask_not_found() -> AppException:
    """Subtask not found"""
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.SUBTASK_NOT_FOUND,
    )


def subtask_access_denied() -> AppException:
    """User doesn't have access to this subtask"""
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ErrorCode.SUBTASK_ACCESS_DENIED,
    )


def invitation_expired() -> AppException:
    """Invitation has expired"""
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.INVITATION_EXPIRED,
    )


def invitation_not_found() -> AppException:
    """Invitation not found or already accepted"""
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.INVITATION_NOT_FOUND,
    )


def invitation_already_sent() -> AppException:
    """An invitation has already been sent to this email"""
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.INVITATION_ALREADY_SENT,
    )


def email_mismatch() -> AppException:
    """Invitation email doesn't match current user's email"""
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ErrorCode.EMAIL_MISMATCH,
    )


def already_member() -> AppException:
    """User is already a member of this project"""
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.ALREADY_MEMBER,
    )


def last_owner() -> AppException:
    """Cannot demote the last owner"""
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.LAST_OWNER,
    )


def cannot_remove_creator() -> AppException:
    """Cannot remove the original project creator"""
    return AppException(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.CANNOT_REMOVE_CREATOR,
    )


def member_not_found() -> AppException:
    """Member not found"""
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ErrorCode.MEMBER_NOT_FOUND,
    )
