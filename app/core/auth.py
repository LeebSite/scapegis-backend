"""
Authentication utilities for OAuth with Supabase
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from supabase import Client
from app.core.database import get_supabase
from app.core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

class AuthService:
    """Service for handling authentication with Supabase"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token from Supabase"""
        try:
            # Get JWT secret from Supabase
            # Note: In production, you should cache this
            response = await self._get_jwt_secret()
            jwt_secret = response.get('jwt_secret')
            
            if not jwt_secret:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            
            # Decode and verify token
            payload = jwt.decode(
                token, 
                jwt_secret, 
                algorithms=[settings.ALGORITHM],
                audience="authenticated"
            )
            
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "authenticated"),
                "exp": payload.get("exp")
            }
            
        except JWTError as e:
            logger.error(f"JWT Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def _get_jwt_secret(self) -> Dict[str, Any]:
        """Get JWT secret from Supabase (cached in production)"""
        # This is a simplified version - in production, implement proper caching
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/",
                headers={"apikey": settings.SUPABASE_ANON_KEY}
            )
            # Note: This is a placeholder - actual implementation depends on Supabase setup
            return {"jwt_secret": settings.SECRET_KEY}
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from user_profiles table"""
        try:
            response = self.supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}")
            return None
    
    async def create_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user profile after OAuth signup"""
        try:
            profile_data = {
                "id": user_data["id"],
                "username": user_data.get("user_metadata", {}).get("preferred_username") or user_data.get("email", "").split("@")[0],
                "full_name": user_data.get("user_metadata", {}).get("full_name") or user_data.get("user_metadata", {}).get("name"),
                "avatar_url": user_data.get("user_metadata", {}).get("avatar_url") or user_data.get("user_metadata", {}).get("picture")
            }
            
            response = self.supabase.table("user_profiles").insert(profile_data).execute()
            
            if response.data:
                return response.data[0]
            
            raise Exception("Failed to create user profile")
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    auth_service = AuthService(supabase)
    user_data = await auth_service.verify_token(credentials.credentials)
    
    # Get user profile
    profile = await auth_service.get_user_profile(user_data["user_id"])
    
    return {
        **user_data,
        "profile": profile
    }


# Dependency to get optional user (for public endpoints)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None


# Dependency for admin users only
async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user if they are admin"""
    
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
