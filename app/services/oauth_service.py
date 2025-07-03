"""
OAuth Service for handling Google and GitHub authentication
"""
import secrets
import httpx
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from fastapi import HTTPException, status
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from supabase import Client
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.auth import AuthService
from app.models.user import UserProfile
import logging

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication with Google and GitHub"""
    
    def __init__(self, supabase: Client, db: Session):
        self.supabase = supabase
        self.db = db
        self.auth_service = AuthService(supabase)
        
        # OAuth client configuration
        self.oauth = OAuth()
        
        # Configure Google OAuth
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.oauth.register(
                name='google',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
        
        # Configure GitHub OAuth
        if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
            self.oauth.register(
                name='github',
                client_id=settings.GITHUB_CLIENT_ID,
                client_secret=settings.GITHUB_CLIENT_SECRET,
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'},
            )
    
    def generate_oauth_url(self, provider: str, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL for the specified provider"""
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        if provider == 'google':
            if not settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Google OAuth not configured"
                )
            
            params = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'scope': 'openid email profile',
                'response_type': 'code',
                'state': state,
                'access_type': 'offline',
                'prompt': 'consent'
            }
            
            oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
            logger.info(f"Generated Google OAuth URL: {oauth_url}")
            logger.info(f"Redirect URI used: {params['redirect_uri']}")
            return oauth_url
        
        elif provider == 'github':
            if not settings.GITHUB_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GitHub OAuth not configured"
                )
            
            params = {
                'client_id': settings.GITHUB_CLIENT_ID,
                'redirect_uri': settings.GITHUB_REDIRECT_URI,
                'scope': 'user:email',
                'state': state,
                'allow_signup': 'true'
            }
            
            return f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
    
    async def exchange_code_for_token(self, provider: str, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        
        try:
            if provider == 'google':
                return await self._exchange_google_code(code)
            elif provider == 'github':
                return await self._exchange_github_code(code)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported OAuth provider: {provider}"
                )
        except Exception as e:
            logger.error(f"Error exchanging code for token ({provider}): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {str(e)}"
            )
    
    async def _exchange_google_code(self, code: str) -> Dict[str, Any]:
        """Exchange Google authorization code for access token"""
        
        token_data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google token exchange failed: {response.text}"
                )
            
            return response.json()
    
    async def _exchange_github_code(self, code: str) -> Dict[str, Any]:
        """Exchange GitHub authorization code for access token"""
        
        token_data = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://github.com/login/oauth/access_token',
                data=token_data,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"GitHub token exchange failed: {response.text}"
                )
            
            return response.json()
    
    async def get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        
        try:
            if provider == 'google':
                return await self._get_google_user_info(access_token)
            elif provider == 'github':
                return await self._get_github_user_info(access_token)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported OAuth provider: {provider}"
                )
        except Exception as e:
            logger.error(f"Error getting user info ({provider}): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user information: {str(e)}"
            )
    
    async def _get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get Google user info: {response.text}"
                )
            
            user_data = response.json()
            
            return {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'avatar': user_data.get('picture'),
                'provider': 'google'
            }
    
    async def _get_github_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from GitHub"""
        
        async with httpx.AsyncClient() as client:
            # Get user profile
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {access_token}'}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get GitHub user info: {user_response.text}"
                )
            
            user_data = user_response.json()
            
            # Get user email (might be private)
            email = user_data.get('email')
            if not email:
                email_response = await client.get(
                    'https://api.github.com/user/emails',
                    headers={'Authorization': f'token {access_token}'}
                )
                
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next((e for e in emails if e.get('primary')), None)
                    if primary_email:
                        email = primary_email.get('email')
            
            return {
                'id': str(user_data.get('id')),
                'email': email,
                'name': user_data.get('name') or user_data.get('login'),
                'avatar': user_data.get('avatar_url'),
                'provider': 'github'
            }

    async def create_or_update_user(self, user_info: Dict[str, Any]) -> Tuple[UserProfile, bool]:
        """Create or update user from OAuth provider data

        Returns:
            Tuple[UserProfile, bool]: (user_profile, is_new_user)
        """

        provider = user_info['provider']
        provider_id = user_info['id']
        email = user_info['email']

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for OAuth authentication"
            )

        try:
            # Check if user exists by provider and provider_id
            existing_user = self.db.query(UserProfile).filter(
                UserProfile.provider == provider,
                UserProfile.provider_id == provider_id
            ).first()

            if existing_user:
                # Update existing user
                existing_user.full_name = user_info.get('name') or existing_user.full_name
                existing_user.avatar_url = user_info.get('avatar') or existing_user.avatar_url
                existing_user.is_verified = True  # OAuth users are considered verified
                self.db.commit()
                self.db.refresh(existing_user)
                return existing_user, False

            # For now, we'll create a new user if not found by provider
            # In the future, you might want to check if user exists by email
            # and link the OAuth account to existing email account

            # Create new user in Supabase Auth
            # Note: We need admin client for user creation
            from app.core.database import get_supabase_admin
            supabase_admin = get_supabase_admin()

            if not supabase_admin:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Admin client not configured"
                )

            auth_response = supabase_admin.auth.admin.create_user({
                "email": email,
                "email_confirm": True,  # Auto-confirm OAuth users
                "user_metadata": {
                    "provider": provider,
                    "provider_id": provider_id,
                    "full_name": user_info.get('name'),
                    "avatar_url": user_info.get('avatar')
                }
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user in Supabase"
                )

            # Create user profile
            user_profile = UserProfile(
                id=auth_response.user.id,
                full_name=user_info.get('name'),
                avatar_url=user_info.get('avatar'),
                provider=provider,
                provider_id=provider_id,
                is_verified=True,
                login_count=1
            )

            self.db.add(user_profile)
            self.db.commit()
            self.db.refresh(user_profile)

            return user_profile, True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/updating OAuth user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create or update user: {str(e)}"
            )

    async def generate_tokens_for_user(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate JWT tokens for authenticated user"""

        # Create access token
        access_token = self.auth_service.create_access_token(
            data={
                "sub": str(user_profile.id),
                "email": user_profile.id,  # We'll get email from Supabase
                "provider": user_profile.provider
            }
        )

        # Create refresh token (simplified - you might want to store this)
        refresh_token = self.auth_service.create_access_token(
            data={
                "sub": str(user_profile.id),
                "type": "refresh"
            },
            expires_delta=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60  # Convert days to minutes
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
