from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime, timedelta
import secrets
import logging
from app.models.user import User, Session, UserCreate, UserLogin, UserResponse, UserRole, SessionResponse, PasswordResetToken, hash_password, verify_password
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class AuthController:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.email_service = EmailService()

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user with hashed password."""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        
        db_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
            phone_country=user_data.phone_country,
            phone_number=user_data.phone_number,
            role=user_data.role or UserRole.user,
            is_active=True
        )
        
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        
        # Send welcome email
        await self.email_service.send_welcome_email(db_user.email, db_user.first_name)
        
        return UserResponse.model_validate(db_user)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return UserResponse.model_validate(user)
        return None

    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """Authenticate user with email and password."""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return UserResponse.model_validate(user)

    async def create_session(self, user_id: int) -> SessionResponse:
        """Create a new session for user."""
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Set expiration (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        db_session = Session(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        
        self.session.add(db_session)
        await self.session.commit()
        await self.session.refresh(db_session)
        
        # Get user data for response
        user = await self.get_user_by_id(user_id)
        
        return SessionResponse(
            id=db_session.id,
            token=db_session.token,
            user_id=db_session.user_id,
            created_at=db_session.created_at,
            expires_at=db_session.expires_at,
            user=user
        )

    async def get_session_by_token(self, token: str) -> Optional[SessionResponse]:
        """Get session by token if not expired."""
        query = select(Session).where(
            and_(
                Session.token == token,
                Session.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Get user data
        user = await self.get_user_by_id(session.user_id)
        if not user:
            return None
        
        return SessionResponse(
            id=session.id,
            token=session.token,
            user_id=session.user_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            user=user
        )

    async def delete_session(self, token: str) -> bool:
        """Delete session by token."""
        query = select(Session).where(Session.token == token)
        result = await self.session.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        await self.session.delete(session)
        await self.session.commit()
        return True

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of deleted sessions."""
        query = select(Session).where(Session.expires_at <= datetime.utcnow())
        result = await self.session.execute(query)
        expired_sessions = result.scalars().all()
        
        count = len(expired_sessions)
        for session in expired_sessions:
            await self.session.delete(session)
        
        await self.session.commit()
        return count

    async def create_password_reset_token(self, email: str) -> bool:
        """Create a password reset token and send email."""
        logger.info(f"Creating password reset token for email: {email}")
        user = await self.get_user_by_email(email)
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return False  # Don't reveal if user exists
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        logger.info(f"Generated password reset token for user {user.id}, expires at {expires_at}")
        
        # Create reset token record
        reset_token = PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at,
            is_used=False
        )
        
        self.session.add(reset_token)
        await self.session.commit()
        logger.info(f"Password reset token saved to database for user {user.id}")
        
        # Send password reset email
        email_sent = await self.email_service.send_password_reset_email(user.email, user.first_name, token)
        
        if email_sent:
            logger.info(f"Password reset email successfully sent to {user.email}")
            return True
        else:
            logger.error(f"Failed to send password reset email to {user.email}")
            return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token."""
        # Find valid token
        query = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > datetime.utcnow(),
                PasswordResetToken.is_used == False
            )
        )
        result = await self.session.execute(query)
        reset_token = result.scalar_one_or_none()
        
        if not reset_token:
            return False
        
        # Get user
        user_query = select(User).where(User.id == reset_token.user_id)
        user_result = await self.session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Update password
        user.hashed_password = hash_password(new_password)
        
        # Mark token as used
        reset_token.is_used = True
        
        await self.session.commit()
        
        # Send confirmation email
        await self.email_service.send_password_reset_confirmation(user.email, user.first_name)
        
        return True

    async def send_login_notification(self, user: UserResponse) -> None:
        """Send login notification email."""
        login_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        await self.email_service.send_login_notification(user.email, user.first_name, login_time)

