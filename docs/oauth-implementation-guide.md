# ScapeGIS OAuth Authentication Guide

## 🎯 Overview

Complete OAuth 2.0 authentication system for ScapeGIS backend with Google and GitHub integration.

## ✨ Features

- ✅ Google OAuth 2.0 integration
- ✅ GitHub OAuth integration
- ✅ JWT token generation and validation
- ✅ User profile management
- ✅ Frontend integration support
- ✅ Database optional mode for testing
- ✅ Comprehensive error handling and security
- ✅ CORS configuration for React frontend

## API Endpoints

### OAuth Initiation
- `GET /api/v1/auth/oauth/google` - Start Google OAuth flow
- `GET /api/v1/auth/oauth/github` - Start GitHub OAuth flow

### OAuth Callbacks
- `GET /api/v1/auth/oauth/callback/google` - Handle Google callback
- `GET /api/v1/auth/oauth/callback/github` - Handle GitHub callback

### User Data
- `GET /api/v1/auth/oauth/user` - Get authenticated user data
- `GET /api/v1/auth/status` - Check authentication status

## Setup Instructions

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# OAuth Redirect URLs
GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/callback/google
GITHUB_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/callback/github

# Frontend URL
FRONTEND_URL=http://localhost:3001

# Supabase (required for user management)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:8001/api/v1/auth/oauth/callback/google`
   - `http://localhost:3001/auth/callback` (for frontend)
7. Copy Client ID and Client Secret to `.env`

### 3. GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in application details:
   - Application name: ScapeGIS
   - Homepage URL: `http://localhost:3001`
   - Authorization callback URL: `http://localhost:8001/api/v1/auth/oauth/callback/github`
4. Copy Client ID and Client Secret to `.env`

### 4. Database Setup

Ensure your user_profiles table supports OAuth:

```sql
-- The table should already have these columns from existing migration
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS provider VARCHAR(20) DEFAULT 'email';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS provider_id VARCHAR(255);
```

## Frontend Integration

### OAuth Flow

1. User clicks OAuth button in frontend
2. Frontend redirects to: `${API_URL}/api/v1/auth/oauth/{provider}`
3. User authorizes with provider
4. Provider redirects to backend callback
5. Backend processes OAuth and redirects to frontend with tokens
6. Frontend extracts tokens and stores them

### Frontend Code Example

```javascript
// Initiate OAuth
const handleOAuthLogin = (provider) => {
  window.location.href = `${process.env.REACT_APP_API_URL}/api/v1/auth/oauth/${provider}`;
};

// Handle callback (in your callback page)
const handleOAuthCallback = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const accessToken = urlParams.get('access_token');
  const refreshToken = urlParams.get('refresh_token');
  const userId = urlParams.get('user_id');
  
  if (accessToken) {
    // Store tokens
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    
    // Get user data
    fetchUserData(accessToken);
  }
};

// Fetch user data
const fetchUserData = async (token) => {
  const response = await fetch(`${API_URL}/api/v1/auth/oauth/user`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  if (data.status === 'success') {
    // Update your auth store with user data
    setUser(data.data.user);
  }
};
```

## Response Format

All OAuth endpoints return data in this format:

```json
{
  "status": "success",
  "data": {
    "access_token": "jwt_token_here",
    "refresh_token": "refresh_token_here",
    "user": {
      "id": "user_id",
      "name": "User Name",
      "email": "user@example.com",
      "avatar": "avatar_url"
    }
  }
}
```

## Error Handling

OAuth errors redirect to: `${FRONTEND_URL}/auth/error?error={error_code}`

Common error codes:
- `oauth_init_failed` - Failed to start OAuth flow
- `no_code` - No authorization code received
- `callback_failed` - Error processing callback
- `{provider_error}` - Provider-specific error

## Security Features

- ✅ State parameter for CSRF protection
- ✅ Secure token handling
- ✅ CORS configuration
- ✅ JWT token expiration
- ✅ User verification for OAuth users
- ✅ Error logging and monitoring

## Testing

### Manual Testing

1. Start the backend: `uvicorn app.main:app --reload --port 8001`
2. Visit: `http://localhost:8001/api/v1/auth/oauth/google`
3. Complete OAuth flow
4. Check redirect to frontend with tokens

### Automated Testing

```bash
# Run OAuth tests
pytest tests/test_oauth.py -v
```

## Troubleshooting

### Common Issues

1. **"OAuth not configured"**
   - Check environment variables are set
   - Verify client IDs and secrets

2. **"Redirect URI mismatch"**
   - Ensure redirect URIs match in OAuth provider settings
   - Check FRONTEND_URL configuration

3. **"User creation failed"**
   - Verify Supabase service role key is set
   - Check database connection

4. **CORS errors**
   - Ensure frontend URL is in ALLOWED_ORIGINS
   - Check CORS middleware configuration

### Debug Mode

Enable debug logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Production Considerations

1. **Security**
   - Use HTTPS for all OAuth URLs
   - Store tokens securely (not in URL params)
   - Implement proper session management
   - Use Redis for temporary token storage

2. **Environment**
   - Update redirect URIs for production domain
   - Use production OAuth app credentials
   - Configure proper CORS origins

3. **Monitoring**
   - Log OAuth events
   - Monitor failed authentication attempts
   - Track user registration metrics
