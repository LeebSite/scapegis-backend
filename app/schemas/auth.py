"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class UserSignupRequest(BaseModel):
    """Schema for user signup request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="User full name")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, one lowercase, and one digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    provider: str
    last_login: Optional[str]
    login_count: int
    created_at: str


class UserPublicResponse(BaseModel):
    """Schema for public user response (limited info)"""
    id: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    provider: str
    created_at: str


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    token: str = Field(..., description="Verification token")


class ResendVerificationRequest(BaseModel):
    """Schema for resend verification email request"""
    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request"""
    token: str = Field(..., description="Reset password token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, one lowercase, and one digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v


class ChangePasswordRequest(BaseModel):
    """Schema for change password request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, one lowercase, and one digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v


class AuthStatusResponse(BaseModel):
    """Schema for authentication status response"""
    authenticated: bool
    user: Optional[UserPublicResponse] = None


class MessageResponse(BaseModel):
    """Schema for simple message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error response"""
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    success: bool = False


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback request"""
    code: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class OAuthProviderResponse(BaseModel):
    """Schema for OAuth provider response"""
    provider: str
    provider_id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    verified: bool = True
