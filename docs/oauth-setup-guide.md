# 🔐 OAuth Setup Guide untuk ScapeGIS Backend

## 1. Setup OAuth Providers di Supabase Dashboard

### A. Google OAuth
1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau pilih existing project
3. Enable Google+ API
4. Buat OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `https://your-project.supabase.co/auth/v1/callback`
5. Copy Client ID dan Client Secret

### B. GitHub OAuth
1. Buka GitHub → Settings → Developer settings → OAuth Apps
2. Klik "New OAuth App"
3. Fill form:
   - Application name: ScapeGIS
   - Homepage URL: `http://localhost:3000` (atau domain production)
   - Authorization callback URL: `https://your-project.supabase.co/auth/v1/callback`
4. Copy Client ID dan Client Secret

### C. Configure di Supabase Dashboard
1. Buka Supabase Dashboard → Authentication → Providers
2. Enable provider yang diinginkan (Google, GitHub, dll)
3. Masukkan Client ID dan Client Secret
4. Set redirect URL: `http://localhost:3000/auth/callback` (untuk development)

## 2. Database Schema untuk User Management

### A. Tabel auth.users (Otomatis dari Supabase)
```sql
-- Tabel ini sudah ada otomatis di Supabase
-- Berisi: id, email, encrypted_password, email_confirmed_at, etc.
```

### B. Tabel user_profiles (Custom - sudah ada di kode Anda)
```sql
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    avatar_url TEXT,
    workspace_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see and edit their own profile
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);
```

### C. Update Projects table untuk user ownership
```sql
-- Sudah ada di kode Anda, pastikan foreign key ke auth.users
ALTER TABLE public.projects 
ADD CONSTRAINT fk_projects_owner 
FOREIGN KEY (owner_id) REFERENCES auth.users(id);

-- Enable RLS untuk projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own projects or public projects
CREATE POLICY "Users can view own projects" ON public.projects
    FOR SELECT USING (auth.uid() = owner_id OR is_public = true);

CREATE POLICY "Users can manage own projects" ON public.projects
    FOR ALL USING (auth.uid() = owner_id);
```

## 3. Backend Implementation

### A. Install dependencies
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### B. Update requirements.txt
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

## 4. Environment Variables
Update `.env` file:
```env
# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Frontend URL for redirects
FRONTEND_URL=http://localhost:3000
```

## 5. Frontend Integration (React)

### A. Install Supabase client
```bash
npm install @supabase/supabase-js
```

### B. Setup Supabase client
```javascript
// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseAnonKey = 'your-anon-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### C. OAuth Login Component
```javascript
// src/components/AuthButton.jsx
import { supabase } from '../lib/supabase'

export function AuthButton() {
  const signInWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
  }

  const signInWithGitHub = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
  }

  return (
    <div>
      <button onClick={signInWithGoogle}>Sign in with Google</button>
      <button onClick={signInWithGitHub}>Sign in with GitHub</button>
    </div>
  )
}
```

## 6. Testing OAuth Flow

1. **Start backend**: `uvicorn app.main:app --reload --port 8001`
2. **Start frontend**: `npm start`
3. **Test OAuth login** melalui frontend
4. **Verify user data** di Supabase Dashboard → Authentication → Users
5. **Check user_profiles table** untuk data tambahan

## 7. Security Best Practices

1. **Enable RLS** pada semua tabel public
2. **Set proper policies** untuk data access
3. **Validate JWT tokens** di backend
4. **Use HTTPS** di production
5. **Set proper CORS** origins
6. **Rotate secrets** regularly

## 8. Troubleshooting

### Common Issues:
- **Redirect URI mismatch**: Pastikan URL callback sama persis
- **CORS errors**: Check allowed origins di Supabase dan FastAPI
- **Token validation**: Pastikan JWT secret benar
- **RLS blocking queries**: Check policies dan user context
