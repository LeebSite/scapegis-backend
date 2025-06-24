# 🗺️ ScapeGIS Backend

Backend API untuk aplikasi GIS menggunakan Python stack dengan FastAPI, PostgreSQL + PostGIS, dan Supabase.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GDAL/OGR system libraries
- PostgreSQL dengan PostGIS extension

### Installation

1. **Clone dan setup virtual environment:**
```bash
git clone <repository-url>
cd scapegis-backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env dengan konfigurasi Supabase Anda
```

4. **Jalankan server:**
```bash
# Option 1: Using startup script (recommended)
python start_server.py

# Option 2: Direct uvicorn command
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Server akan berjalan di http://localhost:8001

## 🔐 OAuth Authentication

### Quick OAuth Test
1. Start the server: `python start_server.py`
2. Open browser: http://localhost:8001/api/v1/auth/oauth/google
3. Complete Google OAuth flow
4. You'll be redirected to frontend with success parameters

### OAuth Endpoints
- **Google OAuth:** `GET /api/v1/auth/oauth/google`
- **GitHub OAuth:** `GET /api/v1/auth/oauth/github`
- **Google Callback:** `GET /api/v1/auth/oauth/callback/google`
- **GitHub Callback:** `GET /api/v1/auth/oauth/callback/github`

## 📚 API Documentation

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **OAuth Test:** http://localhost:8001/api/v1/auth/oauth/google

## 🏗️ Project Structure

```
scapegis-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── core/
│   │   ├── config.py              # Settings & environment
│   │   ├── database.py            # DB connection & Supabase
│   │   └── auth.py                # Auth utilities & JWT
│   ├── models/
│   │   ├── user.py               # User & profile models
│   │   ├── project.py            # Project models
│   │   └── layer.py              # Layer models
│   ├── api/v1/
│   │   ├── auth.py               # OAuth & auth endpoints
│   │   ├── projects.py           # Project CRUD endpoints
│   │   └── layers.py             # Layer CRUD endpoints
│   ├── services/
│   │   ├── oauth_service.py      # OAuth logic (Google/GitHub)
│   │   └── email_service.py      # Email utilities
│   ├── schemas/
│   │   ├── auth.py               # Auth request/response schemas
│   │   ├── project.py            # Project schemas
│   │   └── layer.py              # Layer schemas
│   └── utils/
│       └── responses.py          # API response utilities
├── docs/
│   └── oauth-implementation-guide.md  # OAuth documentation
├── tests/
├── requirements.txt               # All dependencies
├── setup_oauth_database.py       # Database setup script
├── start_server.py               # Universal server startup
└── README.md
```

## 🗄️ Database Setup (Supabase)

1. Buat project di [Supabase](https://supabase.com)
2. Enable PostGIS extension:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```
3. Update `.env` dengan credentials Supabase

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Code formatting
black app/
isort app/

# Linting
flake8 app/
mypy app/
```

## 📖 Documentation

Generate documentation:
```bash
mkdocs serve
```

## 🛠️ Development

### Code Style
- **Formatter:** Black
- **Import sorting:** isort
- **Linting:** flake8
- **Type checking:** mypy

### Git Hooks
```bash
# Install pre-commit hooks
pre-commit install
```

## 🚀 Deployment

### Docker
```bash
docker build -t scapegis-backend .
docker run -p 8000:8000 scapegis-backend
```

### Environment Variables
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `DATABASE_URL`: PostgreSQL connection string

## 📝 License

MIT License
