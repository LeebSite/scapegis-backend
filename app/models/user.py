"""
User Profile Model
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from typing import Dict, Any
from app.core.database import Base


class UserProfile(Base):
    """User Profile model extending Supabase auth.users"""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100))
    avatar_url = Column(Text)
    workspace_id = Column(UUID(as_uuid=True))

    # Email verification fields
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), unique=True)
    verification_token_expires = Column(DateTime(timezone=True))

    # Password reset fields
    reset_password_token = Column(String(255), unique=True)
    reset_password_expires = Column(DateTime(timezone=True))

    # Login tracking
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)

    # OAuth provider info
    provider = Column(String(20), default='email')  # 'email', 'google', 'github', etc.
    provider_id = Column(String(255))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "id": str(self.id),
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "provider": self.provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for public API response (without sensitive data)"""
        return {
            "id": str(self.id),
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "is_verified": self.is_verified,
            "provider": self.provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "id": str(self.id),
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
