from fastapi import APIRouter, Depends, Request
from app.models import UserCreate, UserLogin, User, Token
from app.models.auth import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=User)
async def signup(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a new user account"""
    return await auth_service.signup(user)


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token"""
    return await auth_service.login(user_credentials)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user information"""
    return await auth_service.get_current_user_info(current_user)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request a password reset token to be sent to user's email"""
    # Prefer Origin header, then Referer, then request.base_url
    origin = request.headers.get("origin") or request.headers.get("referer") or str(request.base_url).rstrip("/")
    return await auth_service.forgot_password(payload, origin=origin)


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password using a valid token"""
    return await auth_service.reset_password(payload)
