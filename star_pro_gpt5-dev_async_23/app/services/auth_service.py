from datetime import timedelta, datetime
from typing import Optional
from fastapi import HTTPException, status
from app.models import UserCreate, UserLogin, User, Token, UserInDB
from app.models.auth import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
from app.repositories.user_repository import UserRepository
from app.core.security import security_manager
from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.services.email_service import email_service
import secrets


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def signup(self, user: UserCreate) -> User:
        """Create a new user with business logic validation"""
        try:
            # Check if user already exists
            existing_user = await self.user_repository.get_by_email(user.email)
            if existing_user:
                raise UserAlreadyExistsException()
            
            # Validate password strength
            if not security_manager.validate_password_strength(user.password):
                raise ValueError(f"Password must be at least {security_manager.pwd_context.bcrypt__rounds} characters long")
            
            # Create user in database
            user_in_db = await self.user_repository.create_user(user)
            return self.user_repository.user_in_db_to_user(user_in_db)
            
        except UserAlreadyExistsException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def login(self, user_credentials: UserLogin) -> Token:
        """Authenticate user and return access token"""
        user = await self.user_repository.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            raise InvalidCredentialsException()
        
        # Create access token using configuration; extend to 7 days if remember_me
        access_token_expires = (
            timedelta(minutes=7*24*60)
            if getattr(user_credentials, "remember_me", False)
            else timedelta(minutes=settings.access_token_expire_minutes)
        )
        # access_token_expires = timedelta(minutes=120)
        access_token = security_manager.create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    async def get_current_user_info(self, current_user: UserInDB) -> User:
        """Get current user information"""
        return self.user_repository.user_in_db_to_user(current_user)

    async def forgot_password(self, payload: ForgotPasswordRequest, origin: Optional[str] = None) -> ForgotPasswordResponse:
        """Generate a password reset token and send email via SMTP if configured"""
        user = await self.user_repository.get_by_email(payload.email)
        # To avoid account enumeration, always respond success
        if user:
            token = secrets.token_urlsafe(48)
            expires_at = datetime.utcnow() + timedelta(minutes=settings.reset_token_expire_minutes)
            await self.user_repository.create_password_reset_token(payload.email, token, expires_at)
            # Determine base URL for reset link
            base_url = (origin or settings.frontend_base_url or "http://localhost:3000").rstrip("/")
            reset_link = base_url + f"/reset-password?token={token}"
            # Send email if SMTP configured
            if email_service.is_configured():
                subject = "Reset your password"
                text_body = f"Use the link to reset your password: {reset_link}"
                html_body = f"""
                <p>We received a request to reset your password.</p>
                <p><a href=\"{reset_link}\">Click here to reset your password</a></p>
                <p>If you didn't request this, you can ignore this email.</p>
                <p>Best regards,</p>
                <p>Staicey.ai</p>
                """
                try:
                    email_service.send_email(payload.email, subject, html_body, text_body)
                except Exception:
                    # Do not leak email delivery errors to client; still return success
                    pass
        return ForgotPasswordResponse(message="If an account exists for that email, you'll receive a reset link shortly.")

    async def reset_password(self, payload: ResetPasswordRequest) -> ResetPasswordResponse:
        """Validate reset token and update password"""
        user = await self.user_repository.consume_password_reset_token(payload.token)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
        if not security_manager.validate_password_strength(payload.new_password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password does not meet complexity requirements")
        success = await self.user_repository.update_user_password(user.id, payload.new_password)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password")
        return ResetPasswordResponse(message="Password has been reset successfully.")
