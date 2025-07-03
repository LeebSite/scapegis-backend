"""
Authentication utilities for OAuth and traditional auth with Supabase
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from supabase import Client
from sqlalchemy.orm import Session
from app.core.database import get_supabase, get_db
from app.core.config import settings
from app.models.user import UserProfile
from app.services.email_service import email_service
import httpx
import logging
import secrets

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for handling authentication with Supabase and traditional auth"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # Password utilities
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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

    # ADD THIS NEW METHOD untuk handle OAuth user creation
    async def create_oauth_user_profile(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create user profile specifically for OAuth users"""
        try:
            import uuid
            
            # Generate UUID jika belum ada
            user_id = user_info.get('id') or str(uuid.uuid4())
            
            profile_data = {
                "id": user_id,
                "email": user_info.get("email"),
                "full_name": user_info.get("name", ""),
                "avatar_url": user_info.get("avatar", ""),
                "provider": user_info.get("provider", "oauth"),
                "provider_id": user_info.get("id", "")
            }
            
            logger.info(f"Creating OAuth user profile: {profile_data}")
            
            response = self.supabase.table("user_profiles").insert(profile_data).execute()
            
            if response.data:
                logger.info(f"OAuth user profile created successfully: {response.data[0]}")
                return response.data[0]
            
            raise Exception("Failed to create OAuth user profile")
            
        except Exception as e:
            logger.error(f"Error creating OAuth user profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create OAuth user profile: {str(e)}"
            )

    # ADD THIS NEW METHOD untuk update OAuth user
    async def update_oauth_user_profile(self, user_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing OAuth user profile"""
        try:
            update_data = {
                "full_name": user_info.get("name", ""),
                "avatar_url": user_info.get("avatar", ""),
                "provider": user_info.get("provider", "oauth"),
                "provider_id": user_info.get("id", "")
            }
            
            logger.info(f"Updating OAuth user profile {user_id}: {update_data}")
            
            response = self.supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
            
            if response.data:
                logger.info(f"OAuth user profile updated successfully: {response.data[0]}")
                return response.data[0]
            
            raise Exception("Failed to update OAuth user profile")
            
        except Exception as e:
            logger.error(f"Error updating OAuth user profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update OAuth user profile: {str(e)}"
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


# Tambahkan ini di file auth.py Anda (router endpoints)

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from app.services.oauth_service import OAuthService
from app.core.database import get_supabase, get_db
from app.core.config import settings
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Fungsi helper untuk mendapatkan OAuth service
def get_oauth_service(
    supabase = Depends(get_supabase),
    db = Depends(get_db)
) -> OAuthService:
    return OAuthService(supabase, db)

@router.get("/oauth/callback/google")
async def google_oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """Handle Google OAuth callback"""
    try:
        logger.info(f"Google OAuth callback started with code: {code[:20]}...")
        
        # 1. Exchange authorization code for access token
        logger.info("Exchanging authorization code for access token...")
        token_data = await oauth_service.exchange_code_for_token('google', code)
        
        if not token_data.get('access_token'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received from Google"
            )
        
        # 2. Get user information from Google
        logger.info("Fetching user information from Google...")
        user_info = await oauth_service.get_user_info('google', token_data['access_token'])
        
        if not user_info.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email received from Google"
            )
        
        # 3. Create or update user profile
        logger.info(f"Creating/updating user profile for email: {user_info['email']}")
        user_profile, is_new_user = await oauth_service.create_or_update_user(user_info)
        
        # 4. Generate JWT tokens
        logger.info("Generating JWT tokens...")
        tokens = await oauth_service.generate_tokens_for_user(user_profile)
        
        # 5. PERBAIKAN UTAMA: Gunakan bracket notation untuk dictionary
        response_data = {
            'success': True,
            'user_id': str(user_profile['id']),  # GUNAKAN BRACKET NOTATION
            'email': user_profile['email'],      # GUNAKAN BRACKET NOTATION
            'full_name': user_profile.get('full_name', ''),  # GUNAKAN .get() untuk optional
            'avatar_url': user_profile.get('avatar_url', ''),
            'is_new_user': is_new_user,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in']
        }
        
        logger.info(f"OAuth callback successful for user: {response_data['user_id']}")
        
        # 6. Redirect ke frontend dengan token
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback"
        redirect_url = f"{frontend_url}?token={tokens['access_token']}&success=true"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Redirect ke frontend dengan error
        error_url = f"{settings.FRONTEND_URL}/auth/error"
        redirect_url = f"{error_url}?error=callback_failed&details={str(e)}"
        
        return RedirectResponse(url=redirect_url)

@router.get("/oauth/github")
async def github_oauth_login(oauth_service: OAuthService = Depends(get_oauth_service)):
    """Initiate GitHub OAuth login"""
    try:
        oauth_url = oauth_service.generate_oauth_url('github')
        return RedirectResponse(url=oauth_url)
    except Exception as e:
        logger.error(f"GitHub OAuth initiation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate GitHub OAuth: {str(e)}"
        )

@router.get("/oauth/callback/github")
async def github_oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """Handle GitHub OAuth callback"""
    try:
        logger.info(f"GitHub OAuth callback started with code: {code[:20]}...")
        
        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token('github', code)
        
        # Get user info
        user_info = await oauth_service.get_user_info('github', token_data['access_token'])
        
        # Create or update user
        user_profile, is_new_user = await oauth_service.create_or_update_user(user_info)
        
        # Generate tokens
        tokens = await oauth_service.generate_tokens_for_user(user_profile)
        
        # PERBAIKAN: Gunakan bracket notation untuk dictionary
        response_data = {
            'success': True,
            'user_id': str(user_profile['id']),  # GUNAKAN BRACKET NOTATION
            'email': user_profile['email'],      # GUNAKAN BRACKET NOTATION
            'full_name': user_profile.get('full_name', ''),
            'avatar_url': user_profile.get('avatar_url', ''),
            'is_new_user': is_new_user,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': tokens['token_type'],
            'expires_in': tokens['expires_in']
        }
        
        logger.info(f"GitHub OAuth callback successful for user: {response_data['user_id']}")
        
        # Redirect to frontend with token
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback"
        redirect_url = f"{frontend_url}?token={tokens['access_token']}&success=true"
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Redirect to frontend with error
        error_url = f"{settings.FRONTEND_URL}/auth/error"
        redirect_url = f"{error_url}?error=callback_failed&details={str(e)}"
        
        return RedirectResponse(url=redirect_url)