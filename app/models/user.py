"""
User Profile Model
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class UserProfile(Base):
    """User Profile model extending Supabase auth.users"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100))
    avatar_url = Column(Text)
    workspace_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
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
