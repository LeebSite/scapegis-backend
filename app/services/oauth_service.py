"""
OAuth Service for handling Google and GitHub authentication
"""
import secrets
import httpx
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from datetime import timedelta
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
            try:
                logger.info(f"Registering Google OAuth with client_id: {settings.GOOGLE_CLIENT_ID[:20]}...")
                self.oauth.register(
                    name='google',
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET,
                    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                    client_kwargs={
                        'scope': 'openid email profile'
                    }
                )
                logger.info("Google OAuth registered successfully")
            except Exception as e:
                logger.error(f"Failed to register Google OAuth: {e}")
                raise
        else:
            logger.warning("Google OAuth not configured - missing client_id or client_secret")

        # Configure GitHub OAuth
        if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
            try:
                logger.info("Registering GitHub OAuth...")
                self.oauth.register(
                    name='github',
                    client_id=settings.GITHUB_CLIENT_ID,
                    client_secret=settings.GITHUB_CLIENT_SECRET,
                    access_token_url='https://github.com/login/oauth/access_token',
                    authorize_url='https://github.com/login/oauth/authorize',
                    api_base_url='https://api.github.com/',
                    client_kwargs={'scope': 'user:email'},
                )
                logger.info("GitHub OAuth registered successfully")
            except Exception as e:
                logger.error(f"Failed to register GitHub OAuth: {e}")
                raise
        else:
            logger.warning("GitHub OAuth not configured - missing client_id or client_secret")
    
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

        logger.info(f"Exchanging Google authorization code: {code[:20]}...")

        token_data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        }

        logger.info(f"Token exchange data: {dict(token_data, client_secret='***')}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Accept': 'application/json'}
            )

            logger.info(f"Google token response status: {response.status_code}")
            logger.info(f"Google token response headers: {dict(response.headers)}")

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google token exchange failed: {response.text}"
                )

            token_response = response.json()
            logger.info(f"Token exchange successful: {list(token_response.keys())}")
            return token_response
    
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

        logger.info(f"Fetching Google user info with token: {access_token[:20]}...")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )

            logger.info(f"Google user info response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Failed to get Google user info: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get Google user info: {response.text}"
                )

            user_data = response.json()
            logger.info(f"Google user data received: {user_data}")

            formatted_user_info = {
                'id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'avatar': user_data.get('picture'),
                'provider': 'google'
            }

            logger.info(f"Formatted user info: {formatted_user_info}")
            return formatted_user_info
    
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

    async def create_or_update_user(self, user_info: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Create or update user from OAuth provider data using Supabase

        Returns:
            Tuple[Dict[str, Any], bool]: (user_profile, is_new_user)
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
            logger.info(f"Creating/updating user for provider: {provider}, email: {email}")

            # Check if user exists by email (using Supabase)
            response = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
            existing_user = response.data[0] if response.data else None

            logger.info(f"Existing user found: {existing_user is not None}")

            if existing_user:
                logger.info(f"Updating existing user: {existing_user['id']}")

                # Update existing user using Supabase
                update_data = {
                    'full_name': user_info.get('name') or existing_user.get('full_name'),
                    'avatar_url': user_info.get('avatar') or existing_user.get('avatar_url'),
                    'provider': provider,
                    'provider_id': provider_id
                }

                logger.info(f"Update data: {update_data}")

                response = self.supabase.table('user_profiles').update(update_data).eq('id', existing_user['id']).execute()

                if response.data:
                    logger.info(f"User updated successfully: {response.data[0]}")
                    return response.data[0], False
                else:
                    logger.error("Failed to update user profile - no data returned")
                    raise Exception("Failed to update user profile")

            # Create new user profile using Supabase
            logger.info("Creating new user profile")

            import uuid
            user_id = str(uuid.uuid4())

            new_user_data = {
                'id': user_id,
                'email': email,
                'full_name': user_info.get('name', ''),
                'avatar_url': user_info.get('avatar', ''),
                'provider': provider,
                'provider_id': provider_id
            }

            logger.info(f"New user data: {new_user_data}")

            response = self.supabase.table('user_profiles').insert(new_user_data).execute()

            if response.data:
                logger.info(f"User created successfully: {response.data[0]}")
                return response.data[0], True
            else:
                logger.error("Failed to create user profile - no data returned")
                logger.error(f"Supabase response: {response}")
                raise Exception("Failed to create user profile")

        except Exception as e:
            logger.error(f"Error creating/updating OAuth user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create or update user: {str(e)}"
            )

    async def generate_tokens_for_user(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JWT tokens for authenticated user"""

        logger.info(f"Generating tokens for user profile: {user_profile}")

        # Safely extract user data
        user_id = user_profile.get('id')
        user_email = user_profile.get('email')
        user_provider = user_profile.get('provider', 'oauth')

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User ID is missing from profile"
            )

        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User email is missing from profile"
            )

        # Create access token
        access_token = self.auth_service.create_access_token(
            data={
                "sub": str(user_id),
                "email": user_email,
                "provider": user_provider
            }
        )

        # Create refresh token (simplified - you might want to store this)
        refresh_token = self.auth_service.create_access_token(
            data={
                "sub": str(user_id),
                "type": "refresh"
            },
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
