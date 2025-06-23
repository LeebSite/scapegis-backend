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

async def create_webgis_tables():
    """Buat tabel sesuai spesifikasi frontend WebGIS"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        print("🏗️ Creating WebGIS tables...")

        # Enable UUID extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

        # User profiles table (extends Supabase auth.users)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.user_profiles (
                id UUID REFERENCES auth.users(id) PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                full_name VARCHAR(100),
                avatar_url TEXT,
                workspace_id UUID,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Projects table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.projects (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                workspace_id UUID,
                owner_id UUID REFERENCES auth.users(id),
                settings JSONB DEFAULT '{}',
                bounds GEOMETRY(POLYGON, 4326),
                center GEOMETRY(POINT, 4326),
                zoom_level INTEGER DEFAULT 2,
                is_public BOOLEAN DEFAULT FALSE,
                layer_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Layers table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.layers (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
                layer_type VARCHAR(20) CHECK (layer_type IN ('base', 'vector', 'raster', 'point')),
                data_source TEXT,
                style_config JSONB DEFAULT '{}',
                is_visible BOOLEAN DEFAULT TRUE,
                opacity FLOAT DEFAULT 1.0,
                z_index INTEGER DEFAULT 0,
                bounds GEOMETRY(POLYGON, 4326),
                feature_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Spatial indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_bounds ON public.projects USING GIST (bounds);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_center ON public.projects USING GIST (center);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_layers_bounds ON public.layers USING GIST (bounds);")

        # Regular indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_owner ON public.projects (owner_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_projects_workspace ON public.projects (workspace_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_layers_project ON public.layers (project_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_layers_type ON public.layers (layer_type);")

        print("✅ WebGIS tables berhasil dibuat!")

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
    await create_webgis_tables()
    
    # Test Supabase access
    test_supabase_tables()
    
    print("\n✅ Database setup selesai!")
    print("Selanjutnya Anda bisa:")
    print("1. Update app/core/database.py dengan credentials yang benar")
    print("2. Jalankan server: uvicorn app.main:app --reload")
    print("3. Test API endpoints di http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())
