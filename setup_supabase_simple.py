"""
Simple setup untuk Supabase tables menggunakan SQL commands
"""
from supabase import create_client, Client

# Credentials Supabase
SUPABASE_URL = "https://fgpyqyiazgouorgpkavr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZncHlxeWlhemdvdW9yZ3BrYXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTY4NDgsImV4cCI6MjA2NjI3Mjg0OH0.mi6eHu3jJ9K2RXBz71IKCDNBGs9bnDPBf2a8-IcuvYI"

def create_sample_data():
    """Create sample data untuk testing"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🏗️ Creating sample data...")
        
        # Create sample project
        project_data = {
            "name": "Sample WebGIS Project",
            "description": "A sample project for testing the WebGIS application",
            "settings": {
                "mapCenter": [106.8456, -6.2088],  # Jakarta coordinates
                "mapZoom": 10,
                "bounds": [[106.7, -6.3], [106.9, -6.1]]
            },
            "zoom_level": 10,
            "is_public": True,
            "layer_count": 1
        }
        
        # Insert project
        project_response = supabase.table("projects").insert(project_data).execute()
        
        if project_response.data:
            project_id = project_response.data[0]["id"]
            print(f"✅ Sample project created with ID: {project_id}")
            
            # Create sample layer
            layer_data = {
                "name": "OpenStreetMap Base Layer",
                "description": "Default OpenStreetMap base layer for the project",
                "project_id": project_id,
                "layer_type": "base",
                "data_source": "openstreetmap",
                "style_config": {
                    "type": "raster",
                    "source": {
                        "type": "raster",
                        "tiles": ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                        "tileSize": 256,
                        "attribution": "© OpenStreetMap contributors"
                    }
                },
                "is_visible": True,
                "opacity": 1.0,
                "z_index": 0,
                "feature_count": 0
            }
            
            # Insert layer
            layer_response = supabase.table("layers").insert(layer_data).execute()
            
            if layer_response.data:
                layer_id = layer_response.data[0]["id"]
                print(f"✅ Sample layer created with ID: {layer_id}")
            else:
                print("❌ Failed to create sample layer")
        else:
            print("❌ Failed to create sample project")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

def test_api_endpoints():
    """Test API endpoints dengan sample data"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("\n🧪 Testing API endpoints...")
        
        # Test projects
        projects = supabase.table("projects").select("*").execute()
        print(f"✅ Projects: {len(projects.data)} records")
        
        if projects.data:
            project_id = projects.data[0]["id"]
            
            # Test layers for project
            layers = supabase.table("layers").select("*").eq("project_id", project_id).execute()
            print(f"✅ Layers for project {project_id}: {len(layers.data)} records")
            
            # Show sample project data
            print(f"\n📊 Sample Project Data:")
            print(f"   Name: {projects.data[0]['name']}")
            print(f"   Description: {projects.data[0]['description']}")
            print(f"   Map Center: {projects.data[0]['settings'].get('mapCenter', 'N/A')}")
            print(f"   Map Zoom: {projects.data[0]['settings'].get('mapZoom', 'N/A')}")
            print(f"   Layer Count: {projects.data[0]['layer_count']}")
            
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

def main():
    """Main function"""
    print("🚀 Setting up Supabase with sample data...")
    print("📝 Note: Tables should be created manually in Supabase SQL Editor first")
    print("\nSQL Commands to run in Supabase SQL Editor:")
    print("=" * 60)
    
    sql_commands = """
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- Projects table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    workspace_id UUID,
    owner_id UUID,
    settings JSONB DEFAULT '{}',
    zoom_level INTEGER DEFAULT 2,
    is_public BOOLEAN DEFAULT FALSE,
    layer_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Layers table
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
    feature_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_projects_owner ON public.projects (owner_id);
CREATE INDEX IF NOT EXISTS idx_layers_project ON public.layers (project_id);
"""
    
    print(sql_commands)
    print("=" * 60)
    
    # Ask user if tables are created
    print("\n🔄 Checking if tables exist...")

    # Try to check if tables exist
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("projects").select("count").execute()
        tables_exist = True
        print("✅ Tables already exist!")
    except Exception as e:
        tables_exist = False
        print("❌ Tables don't exist yet")
        print(f"Error: {str(e)[:100]}...")

    if tables_exist:
        # Create sample data
        create_sample_data()
        
        # Test endpoints
        test_api_endpoints()
        
        print("\n🎉 Setup completed!")
        print("\n✅ Your backend is now ready with sample data!")
        print("🌐 You can test the API at: http://localhost:8001/docs")
        print("📊 Frontend can now connect and see sample projects!")
        
    else:
        print("\n📝 Please create the tables first, then run this script again.")

if __name__ == "__main__":
    main()
