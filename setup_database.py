"""
Setup database PostGIS dan tabel untuk ScapeGIS
"""
import asyncio
import asyncpg
from supabase import create_client, Client

# Credentials Supabase
SUPABASE_URL = "https://fgpyqyiazgouorgpkavr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZncHlxeWlhemdvdW9yZ3BrYXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTY4NDgsImV4cCI6MjA2NjI3Mjg0OH0.mi6eHu3jJ9K2RXBz71IKCDNBGs9bnDPBf2a8-IcuvYI"

# Database connection (ganti dengan connection string Supabase Anda)
DATABASE_URL = "postgresql://postgres:your-password@db.fgpyqyiazgouorgpkavr.supabase.co:5432/postgres"

async def setup_postgis():
    """Setup PostGIS extension"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🔧 Setting up PostGIS extension...")
        
        # Enable PostGIS extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis_raster;")
        
        print("✅ PostGIS extension berhasil diaktifkan!")
        
        # Test PostGIS
        version = await conn.fetchval("SELECT PostGIS_Version();")
        print(f"📍 PostGIS Version: {version}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error setup PostGIS: {e}")
        print("Pastikan DATABASE_URL sudah benar dan memiliki permission")

async def create_sample_tables():
    """Buat tabel contoh untuk GIS"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🏗️ Creating sample GIS tables...")
        
        # Tabel Projects
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                bounds GEOMETRY(POLYGON, 4326)
            );
        """)
        
        # Tabel Layers
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS layers (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                name VARCHAR(255) NOT NULL,
                layer_type VARCHAR(50) NOT NULL,
                style_config JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                geom GEOMETRY(GEOMETRY, 4326)
            );
        """)
        
        # Tabel Features (untuk menyimpan fitur GIS)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id SERIAL PRIMARY KEY,
                layer_id INTEGER REFERENCES layers(id),
                properties JSONB,
                geometry GEOMETRY(GEOMETRY, 4326),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Index spatial untuk performa
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_bounds ON projects USING GIST(bounds);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_layers_geom ON layers USING GIST(geom);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_features_geometry ON features USING GIST(geometry);")
        
        print("✅ Sample tables berhasil dibuat!")
        
        # Insert sample data
        await conn.execute("""
            INSERT INTO projects (name, description, bounds) 
            VALUES ('Sample Project', 'Project contoh untuk testing', 
                    ST_GeomFromText('POLYGON((106.8 -6.2, 106.9 -6.2, 106.9 -6.1, 106.8 -6.1, 106.8 -6.2))', 4326))
            ON CONFLICT DO NOTHING;
        """)
        
        print("✅ Sample data berhasil diinsert!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

def test_supabase_tables():
    """Test query tabel melalui Supabase client"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🧪 Testing Supabase table access...")
        
        # Test query projects
        response = supabase.table("projects").select("*").execute()
        print(f"✅ Projects table: {len(response.data)} records")
        
        # Test query layers
        response = supabase.table("layers").select("*").execute()
        print(f"✅ Layers table: {len(response.data)} records")
        
        # Test query features
        response = supabase.table("features").select("*").execute()
        print(f"✅ Features table: {len(response.data)} records")
        
        print("🎉 Database setup lengkap!")
        
    except Exception as e:
        print(f"❌ Error testing tables: {e}")

async def main():
    """Main function"""
    print("🚀 Starting database setup...")
    
    # Setup PostGIS
    await setup_postgis()
    
    # Create tables
    await create_sample_tables()
    
    # Test Supabase access
    test_supabase_tables()
    
    print("\n✅ Database setup selesai!")
    print("Selanjutnya Anda bisa:")
    print("1. Update app/core/database.py dengan credentials yang benar")
    print("2. Jalankan server: uvicorn app.main:app --reload")
    print("3. Test API endpoints di http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())
