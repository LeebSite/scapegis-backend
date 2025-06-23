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
pip install -r requirements-dev.txt
# pip install -r requirements-gis.txt  # Setelah GDAL terinstall
```

3. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env dengan konfigurasi Supabase Anda
```

4. **Jalankan server:**
```bash
uvicorn app.main:app --reload
```

Server akan berjalan di http://localhost:8000

## 📚 API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🏗️ Project Structure

```
scapegis-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── core/
│   │   ├── config.py           # Settings
│   │   ├── database.py         # DB connection
│   │   └── security.py         # Auth utilities
│   ├── models/
│   │   ├── user.py            # User models
│   │   ├── project.py         # Project models
│   │   └── spatial.py         # Spatial models
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py        # Auth endpoints
│   │       ├── projects.py    # Project endpoints
│   │       └── spatial.py     # Spatial endpoints
│   ├── services/
│   │   ├── auth_service.py    # Auth logic
│   │   └── gis_service.py     # GIS operations
│   └── utils/
│       └── spatial.py         # Spatial utilities
├── tests/
├── requirements.txt
├── requirements-dev.txt
├── requirements-gis.txt
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
