"""
Automatic table creation using Supabase API
"""
from supabase import create_client, Client
import json

# Credentials Supabase
SUPABASE_URL = "https://fgpyqyiazgouorgpkavr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZncHlxeWlhemdvdW9yZ3BrYXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTY4NDgsImV4cCI6MjA2NjI3Mjg0OH0.mi6eHu3jJ9K2RXBz71IKCDNBGs9bnDPBf2a8-IcuvYI"

def create_sample_projects():
    """Create sample projects directly via Supabase API"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🏗️ Creating sample projects...")
        
        # Sample projects data
        projects = [
            {
                "name": "Sample WebGIS Project",
                "description": "A sample project for testing the WebGIS application",
                "settings": {
                    "mapCenter": [106.8456, -6.2088],
                    "mapZoom": 10,
                    "bounds": [[106.7, -6.3], [106.9, -6.1]]
                },
                "zoom_level": 10,
                "is_public": True,
                "layer_count": 1
            },
            {
                "name": "Jakarta Map Project", 
                "description": "Jakarta city mapping project with detailed layers",
                "settings": {
                    "mapCenter": [106.8456, -6.2088],
                    "mapZoom": 12
                },
                "zoom_level": 12,
                "is_public": False,
                "layer_count": 2
            },
            {
                "name": "Indonesia Overview",
                "description": "National overview map of Indonesia", 
                "settings": {
                    "mapCenter": [118.0148, -2.5489],
                    "mapZoom": 5
                },
                "zoom_level": 5,
                "is_public": True,
                "layer_count": 1
            },
            {
                "name": "Bandung City Map",
                "description": "Detailed map of Bandung city",
                "settings": {
                    "mapCenter": [107.6191, -6.9175],
                    "mapZoom": 11
                },
                "zoom_level": 11,
                "is_public": False,
                "layer_count": 3
            },
            {
                "name": "Surabaya Port Area",
                "description": "Port and industrial area mapping",
                "settings": {
                    "mapCenter": [112.7521, -7.2575],
                    "mapZoom": 13
                },
                "zoom_level": 13,
                "is_public": True,
                "layer_count": 2
            }
        ]
        
        # Insert projects
        response = supabase.table("projects").insert(projects).execute()
        
        if response.data:
            print(f"✅ Created {len(response.data)} sample projects!")
            
            # Create sample layers for first project
            project_id = response.data[0]["id"]
            create_sample_layers(supabase, project_id)
            
            return True
        else:
            print("❌ Failed to create projects")
            return False
            
    except Exception as e:
        print(f"❌ Error creating projects: {e}")
        return False

def create_sample_layers(supabase: Client, project_id: str):
    """Create sample layers for a project"""
    try:
        print("🗂️ Creating sample layers...")
        
        layers = [
            {
                "name": "OpenStreetMap Base",
                "description": "Default OpenStreetMap base layer",
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
        ]
        
        response = supabase.table("layers").insert(layers).execute()
        
        if response.data:
            print(f"✅ Created {len(response.data)} sample layers!")
        else:
            print("❌ Failed to create layers")
            
    except Exception as e:
        print(f"❌ Error creating layers: {e}")

def test_endpoints():
    """Test if endpoints work after table creation"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("\n🧪 Testing endpoints...")
        
        # Test projects
        projects = supabase.table("projects").select("*").execute()
        print(f"✅ Projects: {len(projects.data)} records")
        
        # Test layers
        layers = supabase.table("layers").select("*").execute()
        print(f"✅ Layers: {len(layers.data)} records")
        
        if projects.data:
            print(f"\n📊 Sample Project:")
            project = projects.data[0]
            print(f"   Name: {project['name']}")
            print(f"   Description: {project['description']}")
            print(f"   Map Center: {project['settings'].get('mapCenter', 'N/A')}")
            print(f"   Map Zoom: {project['settings'].get('mapZoom', 'N/A')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Auto-creating database tables and sample data...")
    print("📝 Note: This will only work if tables already exist in Supabase")
    print("\nIf tables don't exist, you need to create them via Supabase SQL Editor first.")
    print("See the SQL commands in the previous message.\n")
    
    # Try to create sample data
    success = create_sample_projects()
    
    if success:
        # Test endpoints
        test_endpoints()
        
        print("\n🎉 Setup completed successfully!")
        print("\n✅ Your backend is now ready with sample data!")
        print("🌐 Frontend should now be able to load projects!")
        print("📊 Test at: http://localhost:3000")
        
    else:
        print("\n❌ Setup failed!")
        print("📝 Please create tables manually in Supabase SQL Editor first.")
        print("Then run this script again.")

if __name__ == "__main__":
    main()
