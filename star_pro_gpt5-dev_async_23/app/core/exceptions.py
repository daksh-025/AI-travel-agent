from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class AuthException(HTTPException):
    """Base authentication exception"""
    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: str = "Authentication failed",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UserNotFoundException(AuthException):
    """Raised when user is not found"""
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsException(AuthException):
    """Raised when trying to create a user that already exists"""
    def __init__(self, detail: str = "User with this email already exists"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidCredentialsException(AuthException):
    """Raised when login credentials are invalid"""
    def __init__(self, detail: str = "Incorrect email or password"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenException(AuthException):
    """Raised when token is invalid or expired"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ValidationException(HTTPException):
    """Raised when input validation fails"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
