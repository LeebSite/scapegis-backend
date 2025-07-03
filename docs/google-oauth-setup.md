# Google OAuth Setup untuk ScapeGIS Backend

## Masalah yang Diperbaiki

Error `redirect_uri_mismatch` terjadi karena ketidaksesuaian antara redirect URI yang dikonfigurasi di Google Cloud Console dengan yang digunakan di backend.

## Konfigurasi Google Cloud Console yang Benar

### 1. Authorized JavaScript Origins
```
http://localhost:3001
http://localhost:8001
https://fgpyqyiazgouorgpkavr.supabase.co
```

### 2. Authorized Redirect URIs
```
http://localhost:8001/api/v1/auth/oauth/callback/google
http://localhost:3001/auth/callback
https://fgpyqyiazgouorgpkavr.supabase.co/auth/v1/callback
```

## Konfigurasi Backend (.env)

```env
# OAuth Configuration
GOOGLE_CLIENT_ID=940830341579-0fcheup5gm7naos0cubblmueftb6viqp.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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

# OAuth Redirect URIs
GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/callback/google

# Frontend URL for redirect after OAuth
FRONTEND_URL=http://localhost:3001
```

## Endpoint OAuth Backend

### Initiate OAuth
- **URL**: `GET /api/v1/auth/oauth/google`
- **Deskripsi**: Memulai flow OAuth Google
- **Redirect**: Mengarahkan ke Google OAuth consent screen

### OAuth Callback
- **URL**: `GET /api/v1/auth/oauth/callback/google`
- **Deskripsi**: Menangani callback dari Google setelah user authorize
- **Parameters**: 
  - `code`: Authorization code dari Google
  - `state`: State parameter untuk security
  - `error`: Error parameter jika ada masalah

## Flow OAuth yang Benar

1. **Frontend** → `http://localhost:8001/api/v1/auth/oauth/google`
2. **Backend** → Redirect ke Google OAuth consent screen
3. **Google** → User authorize aplikasi
4. **Google** → Redirect ke `http://localhost:8001/api/v1/auth/oauth/callback/google?code=...`
5. **Backend** → Exchange code untuk access token
6. **Backend** → Get user info dari Google
7. **Backend** → Create/update user di database
8. **Backend** → Generate JWT tokens
9. **Backend** → Redirect ke `http://localhost:3001/auth/callback?access_token=...&user_id=...`

## Testing OAuth

### 1. Start Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Test OAuth Initiation
```bash
curl -X GET "http://localhost:8001/api/v1/auth/oauth/google"
```

### 3. Check Logs
Backend akan menampilkan log untuk setiap step OAuth flow.

## Troubleshooting

### Error: redirect_uri_mismatch
- Pastikan redirect URI di Google Cloud Console sama persis dengan `GOOGLE_REDIRECT_URI` di .env
- Pastikan tidak ada trailing slash atau perbedaan case

### Error: invalid_client
- Pastikan `GOOGLE_CLIENT_ID` dan `GOOGLE_CLIENT_SECRET` benar
- Pastikan credentials tidak expired

### Error: access_denied
- User menolak authorization
- Normal behavior, tidak perlu diperbaiki

## Supabase Configuration

### Site URL
```
http://localhost:3001
```

### Redirect URLs
```
http://localhost:3001/auth/callback
http://localhost:3001/dashboard
http://localhost:3001/
```

Konfigurasi Supabase ini untuk OAuth yang dihandle langsung oleh Supabase client-side, berbeda dengan OAuth yang dihandle oleh backend FastAPI.
