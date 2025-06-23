"""
Authentication API endpoints
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from supabase import Client
from app.core.database import get_supabase
from app.core.auth import get_current_user, get_current_user_optional, AuthService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic models
class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    user: Dict[str, Any]
    session: Optional[Dict[str, Any]] = None
    message: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    created_at: str


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current authenticated user information"""
    
    profile = current_user.get("profile", {})
    
    return UserResponse(
        id=current_user["user_id"],
        email=current_user["email"],
        username=profile.get("username"),
        full_name=profile.get("full_name"),
        avatar_url=profile.get("avatar_url"),
        created_at=profile.get("created_at", "")
    )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Update user profile"""
    
    try:
        # Prepare update data
        update_data = {}
        if profile_update.username is not None:
            update_data["username"] = profile_update.username
        if profile_update.full_name is not None:
            update_data["full_name"] = profile_update.full_name
        if profile_update.avatar_url is not None:
            update_data["avatar_url"] = profile_update.avatar_url
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update profile in database
        response = supabase.table("user_profiles").update(update_data).eq("id", current_user["user_id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        updated_profile = response.data[0]
        
        return UserResponse(
            id=current_user["user_id"],
            email=current_user["email"],
            username=updated_profile.get("username"),
            full_name=updated_profile.get("full_name"),
            avatar_url=updated_profile.get("avatar_url"),
            created_at=updated_profile.get("created_at", "")
        )
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/callback")
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """Handle OAuth callback from providers"""
    
    if error:
        logger.error(f"OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error={error}",
            status_code=status.HTTP_302_FOUND
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # Exchange code for session (handled by Supabase client-side)
        # This endpoint is mainly for handling redirects
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/success",
            status_code=status.HTTP_302_FOUND
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=callback_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Logout current user"""
    
    try:
        # Supabase handles logout client-side, but we can log the event
        logger.info(f"User {current_user['user_id']} logged out")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/status")
async def auth_status(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Check authentication status"""
    
    if current_user:
        profile = current_user.get("profile", {})
        return {
            "authenticated": True,
            "user": {
                "id": current_user["user_id"],
                "email": current_user["email"],
                "username": profile.get("username"),
                "full_name": profile.get("full_name"),
                "avatar_url": profile.get("avatar_url")
            }
        }
    
    return {"authenticated": False, "user": None}


@router.post("/setup-profile")
async def setup_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Setup user profile after first OAuth login"""
    
    try:
        auth_service = AuthService(supabase)
        
        # Check if profile already exists
        existing_profile = await auth_service.get_user_profile(current_user["user_id"])
        
        if existing_profile:
            return {
                "message": "Profile already exists",
                "profile": existing_profile
            }
        
        # Create new profile
        # Note: This would typically get user data from the JWT or Supabase auth
        user_data = {
            "id": current_user["user_id"],
            "email": current_user["email"]
        }
        
        profile = await auth_service.create_user_profile(user_data)
        
        return {
            "message": "Profile created successfully",
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"Error setting up user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup profile"
        )
