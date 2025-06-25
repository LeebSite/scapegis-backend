"""
Authentication API endpoints
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from supabase import Client
from sqlalchemy.orm import Session
from app.core.database import get_supabase, get_db, get_db_optional
from app.core.auth import get_current_user, get_current_user_optional, AuthService
from app.core.config import settings
from app.models.user import UserProfile
from app.schemas.auth import (
    UserSignupRequest, UserLoginRequest, UserResponse, AuthResponse,
    UserProfileUpdate, EmailVerificationRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    AuthStatusResponse, MessageResponse, UserPublicResponse
)
from app.services.email_service import email_service
from app.services.oauth_service import OAuthService
import logging
import secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Helper functions
async def get_user_by_email(db: Session, email: str) -> Optional[UserProfile]:
    """Get user by email from database"""
    try:
        # First try to get from Supabase auth.users
        supabase = get_supabase()
        auth_response = supabase.auth.admin.list_users()

        auth_user = None
        for user in auth_response.users:
            if user.email == email:
                auth_user = user
                break

        if not auth_user:
            return None

        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.id == auth_user.id).first()
        return profile

    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None


async def create_user_with_profile(db: Session, supabase: Client, email: str, password: str, full_name: Optional[str] = None) -> UserProfile:
    """Create user in Supabase auth and profile in database"""
    try:
        # Create user in Supabase auth
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": False  # We'll handle email verification manually
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        # Generate verification token
        verification_token = email_service.generate_verification_token()
        verification_expires = email_service.get_token_expiry(24)  # 24 hours

        # Create user profile
        user_profile = UserProfile(
            id=auth_response.user.id,
            username=email.split('@')[0],  # Default username from email
            full_name=full_name,
            is_verified=False,
            verification_token=verification_token,
            verification_token_expires=verification_expires,
            provider='email'
        )

        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)

        return user_profile

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


# API Endpoints

@router.post("/signup", response_model=MessageResponse)
async def signup(
    user_data: UserSignupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    supabase: Client = Depends(get_supabase)
):
    """User signup endpoint"""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user with profile
        user_profile = await create_user_with_profile(
            db, supabase, user_data.email, user_data.password, user_data.full_name
        )

        # Send verification email in background
        background_tasks.add_task(
            email_service.send_verification_email,
            user_data.email,
            user_profile.verification_token,
            user_profile.full_name
        )

        return MessageResponse(
            message="Account created successfully. Please check your email to verify your account.",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    user_data: UserLoginRequest,
    db: Session = Depends(get_db),
    supabase: Client = Depends(get_supabase)
):
    """User login endpoint"""
    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Get user profile
        user_profile = db.query(UserProfile).filter(
            UserProfile.id == auth_response.user.id
        ).first()

        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        # Check if email is verified (for email provider)
        if user_profile.provider == 'email' and not user_profile.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email address before logging in"
            )

        # Update login tracking
        user_profile.last_login = datetime.utcnow()
        user_profile.login_count += 1
        db.commit()

        # Create custom JWT token
        auth_service = AuthService(supabase)
        access_token = auth_service.create_access_token(
            data={"sub": str(auth_response.user.id), "email": auth_response.user.email}
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user_profile.id),
                email=auth_response.user.email,
                username=user_profile.username,
                full_name=user_profile.full_name,
                avatar_url=user_profile.avatar_url,
                is_verified=user_profile.is_verified,
                provider=user_profile.provider,
                last_login=user_profile.last_login.isoformat() if user_profile.last_login else None,
                login_count=user_profile.login_count,
                created_at=user_profile.created_at.isoformat()
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/verify")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Email verification endpoint"""
    try:
        # Find user by verification token
        user_profile = db.query(UserProfile).filter(
            UserProfile.verification_token == token
        ).first()

        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        # Check if token is expired
        if user_profile.verification_token_expires and user_profile.verification_token_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )

        # Verify user
        user_profile.is_verified = True
        user_profile.verification_token = None
        user_profile.verification_token_expires = None
        db.commit()

        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/verified",
            status_code=status.HTTP_302_FOUND
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/verification-error",
            status_code=status.HTTP_302_FOUND
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


# OAuth Endpoints
@router.get("/oauth/google")
async def google_oauth_initiate(
    db: Session = Depends(get_db_optional),
    supabase: Client = Depends(get_supabase)
):
    """Initiate Google OAuth flow"""

    try:
        # Check if database is available
        if db is None:
            logger.warning("Database not configured - using simplified OAuth flow")

        oauth_service = OAuthService(supabase, db)

        # Generate OAuth URL
        oauth_url = oauth_service.generate_oauth_url('google')

        return RedirectResponse(
            url=oauth_url,
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        logger.error(f"Google OAuth initiation error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=oauth_init_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.get("/oauth/github")
async def github_oauth_initiate(
    db: Session = Depends(get_db_optional),
    supabase: Client = Depends(get_supabase)
):
    """Initiate GitHub OAuth flow"""

    try:
        # Check if database is available
        if db is None:
            logger.warning("Database not configured - using simplified OAuth flow")

        oauth_service = OAuthService(supabase, db)

        # Generate OAuth URL
        oauth_url = oauth_service.generate_oauth_url('github')

        return RedirectResponse(
            url=oauth_url,
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        logger.error(f"GitHub OAuth initiation error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=oauth_init_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.get("/oauth/callback/google")
async def google_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db_optional),
    supabase: Client = Depends(get_supabase)
):
    """Handle Google OAuth callback"""

    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error={error}",
            status_code=status.HTTP_302_FOUND
        )

    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=no_code",
            status_code=status.HTTP_302_FOUND
        )

    try:
        # Check if database is available
        if db is None:
            logger.warning("Database not configured - using simplified OAuth flow")
            # For simplified flow, redirect to /auth/callback with dummy data
            from urllib.parse import urlencode
            token_params = urlencode({
                'access_token': 'dummy',
                'refresh_token': 'dummy',
                'user_id': 'dummy',
                'email': 'dummy@example.com',
                'name': 'Dummy User',
                'avatar_url': '',
                'oauth_success': 'false',
                'provider': 'google',
                'message': 'login_failed_no_db'
            })
            redirect_url = f"{settings.FRONTEND_URL}/auth/callback?{token_params}"
            return RedirectResponse(
                url=redirect_url,
                status_code=status.HTTP_302_FOUND
            )

        oauth_service = OAuthService(supabase, db)

        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token('google', code)

        # Get user info
        user_info = await oauth_service.get_user_info('google', token_data['access_token'])

        # Create or update user profile
        user_profile = await oauth_service.create_or_update_oauth_user('google', user_info)

        # Generate JWT tokens
        tokens = await oauth_service.generate_tokens_for_user(user_profile)

        # Redirect to frontend with tokens and user info
        from urllib.parse import urlencode
        token_params = urlencode({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user_id': str(user_profile.id),
            'email': user_profile.email,
            'name': user_profile.full_name,
            'avatar_url': user_profile.avatar_url,
            'oauth_success': 'true',
            'provider': 'google',
            'message': 'login_successful'
        })
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?{token_params}"

        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=callback_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.get("/oauth/callback/github")
async def github_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db_optional),
    supabase: Client = Depends(get_supabase)
):
    """Handle GitHub OAuth callback"""

    if error:
        logger.error(f"GitHub OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error={error}",
            status_code=status.HTTP_302_FOUND
        )

    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=no_code",
            status_code=status.HTTP_302_FOUND
        )

    try:
        # Check if database is available
        if db is None:
            logger.warning("Database not configured - using simplified OAuth flow")
            # For simplified flow, redirect directly to dashboard with success message
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/dashboard?oauth_success=true&provider=github&message=login_successful",
                status_code=status.HTTP_302_FOUND
            )

        oauth_service = OAuthService(supabase, db)

        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token('github', code)

        # Get user info
        user_info = await oauth_service.get_user_info('github', token_data['access_token'])

        # Create or update user profile
        user_profile = await oauth_service.create_or_update_oauth_user('github', user_info)

        # Generate JWT tokens
        tokens = await oauth_service.generate_tokens_for_user(user_profile)

        # Redirect to frontend with tokens
        from urllib.parse import urlencode
        token_params = urlencode({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user_id': str(user_profile.id)
        })
        redirect_url = f"{settings.FRONTEND_URL}/auth/callback?success=true&provider=github"
        redirect_url += f"&{token_params}"

        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {e}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?error=callback_failed",
            status_code=status.HTTP_302_FOUND
        )


@router.post("/callback")
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """Handle OAuth callback from providers (legacy endpoint)"""

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
