from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, func, Enum as SQLEnum
import bcrypt

class PhoneCountry(str, Enum):
    au = "au"
    ph = "ph"

class UserRole(str, Enum):
    """User role enumeration."""
    user = "user"
    admin = "admin"

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    phone_country: Optional[PhoneCountry] = None
    phone_number: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = True
    is_admin: bool = Field(default=False)
    role: UserRole = Field(
        default=UserRole.user,
        sa_column=Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]))
    )
    # Profile attributes
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

class UserCreate(SQLModel):
    email: str
    first_name: str
    last_name: str
    password: str
    phone_country: PhoneCountry
    phone_number: str
    role: Optional[UserRole] = Field(default=UserRole.user)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserLogin(SQLModel):
    email: str
    password: str

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    expires_at: datetime

    class Config:
        from_attributes = True

class SessionResponse(SQLModel):
    id: int
    token: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True

class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    expires_at: datetime
    is_used: bool = False

class PasswordResetRequest(SQLModel):
    email: str

class PasswordResetConfirm(SQLModel):
    token: str
    new_password: str

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

