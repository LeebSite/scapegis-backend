# 🔧 Perbaikan OAuth Google - ScapeGIS Backend

## ❌ Masalah
Error `redirect_uri_mismatch` karena ketidaksesuaian redirect URI antara Google Cloud Console dan backend.

## ✅ Solusi yang Sudah Diterapkan di Backend

### 1. File `.env` sudah diperbaiki:
```env
GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/callback/google
```

### 2. Endpoint OAuth sudah benar:
- **Initiate**: `GET /api/v1/auth/oauth/google`
- **Callback**: `GET /api/v1/auth/oauth/callback/google`

### 3. Backend menghasilkan URL OAuth yang benar:
```
https://accounts.google.com/o/oauth2/v2/auth?
client_id=940830341579-0fcheup5gm7naos0cubblmueftb6viqp.apps.googleusercontent.com
&redirect_uri=http://localhost:8001/api/v1/auth/oauth/callback/google
&scope=openid+email+profile
&response_type=code
&access_type=offline
&prompt=consent
```

## 🚨 YANG PERLU ANDA LAKUKAN

### Update Google Cloud Console:

1. **Buka**: https://console.cloud.google.com/
2. **Pilih project**: ScapeGIS Backend
3. **Navigasi**: APIs & Services → Credentials
4. **Edit**: OAuth 2.0 Client ID yang sudah ada
5. **Update Authorized redirect URIs** menjadi:

```
http://localhost:8001/api/v1/auth/oauth/callback/google
http://localhost:3001/auth/callback
https://fgpyqyiazgouorgpkavr.supabase.co/auth/v1/callback
```

6. **Simpan** perubahan

### Konfigurasi yang Benar:

#### Authorized JavaScript Origins:
```
http://localhost:3001
http://localhost:8001
https://fgpyqyiazgouorgpkavr.supabase.co
```

#### Authorized Redirect URIs:
```
http://localhost:8001/api/v1/auth/oauth/callback/google
http://localhost:3001/auth/callback
https://fgpyqyiazgouorgpkavr.supabase.co/auth/v1/callback
```

## 🧪 Testing

Setelah update Google Cloud Console:

1. **Start backend**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **Test OAuth flow**:
   - Buka browser: `http://localhost:8001/api/v1/auth/oauth/google`
   - Seharusnya redirect ke Google consent screen tanpa error
   - Setelah authorize, akan redirect ke callback endpoint

## 📝 Catatan

- Backend sudah diperbaiki dan siap digunakan
- Hanya perlu update konfigurasi di Google Cloud Console
- Setelah update, OAuth flow akan berfungsi normal
- Logging sudah ditambahkan untuk debugging

## 🔍 Debugging

Jika masih ada masalah, check log backend untuk melihat:
- URL OAuth yang dihasilkan
- Redirect URI yang digunakan
- Error messages dari Google

Backend akan menampilkan log seperti:
```
INFO: Generated Google OAuth URL: https://accounts.google.com/o/oauth2/v2/auth?...
INFO: Redirect URI used: http://localhost:8001/api/v1/auth/oauth/callback/google
```
