"""
Setup database untuk OAuth authentication dengan Supabase
"""
import asyncio
import asyncpg
from supabase import create_client, Client

# Credentials Supabase (ganti dengan credentials Anda)
SUPABASE_URL = "https://fgpyqyiazgouorgpkavr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZncHlxeWlhemdvdW9yZ3BrYXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTY4NDgsImV4cCI6MjA2NjI3Mjg0OH0.mi6eHu3jJ9K2RXBz71IKCDNBGs9bnDPBf2a8-IcuvYI"

# Database connection (ganti dengan connection string Anda)
DATABASE_URL = "postgresql://postgres:your-password@db.fgpyqyiazgouorgpkavr.supabase.co:5432/postgres"

async def setup_oauth_tables():
    """Setup tabel dan policies untuk OAuth authentication"""
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("🔗 Connected to database")
        
        # 1. Create user_profiles table
        print("📝 Creating user_profiles table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.user_profiles (
                id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                full_name VARCHAR(100),
                avatar_url TEXT,
                workspace_id UUID,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # 2. Create indexes for better performance
        print("🔍 Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_profiles_username 
            ON public.user_profiles(username);
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_profiles_workspace 
            ON public.user_profiles(workspace_id);
        """)
        
        # 3. Enable Row Level Security (RLS)
        print("🔒 Enabling Row Level Security...")
        await conn.execute("""
            ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
        """)
        
        # 4. Create RLS policies for user_profiles
        print("📋 Creating RLS policies for user_profiles...")
        
        # Policy: Users can view their own profile
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can view own profile" ON public.user_profiles;
            CREATE POLICY "Users can view own profile" ON public.user_profiles
                FOR SELECT USING (auth.uid() = id);
        """)
        
        # Policy: Users can update their own profile
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
            CREATE POLICY "Users can update own profile" ON public.user_profiles
                FOR UPDATE USING (auth.uid() = id);
        """)
        
        # Policy: Users can insert their own profile
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can insert own profile" ON public.user_profiles;
            CREATE POLICY "Users can insert own profile" ON public.user_profiles
                FOR INSERT WITH CHECK (auth.uid() = id);
        """)
        
        # 5. Update projects table RLS
        print("🗂️ Setting up projects table RLS...")
        await conn.execute("""
            ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
        """)
        
        # Policy: Users can view their own projects or public projects
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can view projects" ON public.projects;
            CREATE POLICY "Users can view projects" ON public.projects
                FOR SELECT USING (auth.uid() = owner_id OR is_public = true);
        """)
        
        # Policy: Users can manage their own projects
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can manage own projects" ON public.projects;
            CREATE POLICY "Users can manage own projects" ON public.projects
                FOR ALL USING (auth.uid() = owner_id);
        """)
        
        # 6. Update layers table RLS
        print("🗺️ Setting up layers table RLS...")
        await conn.execute("""
            ALTER TABLE public.layers ENABLE ROW LEVEL SECURITY;
        """)
        
        # Policy: Users can view layers of projects they own or public projects
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can view layers" ON public.layers;
            CREATE POLICY "Users can view layers" ON public.layers
                FOR SELECT USING (
                    EXISTS (
                        SELECT 1 FROM public.projects 
                        WHERE projects.id = layers.project_id 
                        AND (projects.owner_id = auth.uid() OR projects.is_public = true)
                    )
                );
        """)
        
        # Policy: Users can manage layers of their own projects
        await conn.execute("""
            DROP POLICY IF EXISTS "Users can manage layers" ON public.layers;
            CREATE POLICY "Users can manage layers" ON public.layers
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM public.projects 
                        WHERE projects.id = layers.project_id 
                        AND projects.owner_id = auth.uid()
                    )
                );
        """)
        
        # 7. Create function to handle user profile creation
        print("⚙️ Creating trigger function for user profile creation...")
        await conn.execute("""
            CREATE OR REPLACE FUNCTION public.handle_new_user()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO public.user_profiles (id, username, full_name, avatar_url)
                VALUES (
                    NEW.id,
                    COALESCE(NEW.raw_user_meta_data->>'preferred_username', split_part(NEW.email, '@', 1)),
                    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
                    COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture')
                );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """)
        
        # 8. Create trigger to automatically create user profile
        await conn.execute("""
            DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
            CREATE TRIGGER on_auth_user_created
                AFTER INSERT ON auth.users
                FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
        """)
        
        # 9. Grant necessary permissions
        print("🔑 Granting permissions...")
        await conn.execute("""
            GRANT USAGE ON SCHEMA public TO anon, authenticated;
            GRANT ALL ON public.user_profiles TO anon, authenticated;
            GRANT ALL ON public.projects TO anon, authenticated;
            GRANT ALL ON public.layers TO anon, authenticated;
        """)
        
        await conn.close()
        print("✅ OAuth database setup completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up OAuth database: {e}")
        return False


def test_supabase_connection():
    """Test Supabase connection"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test connection by fetching projects
        response = supabase.table("projects").select("id, name").limit(1).execute()
        
        print("✅ Supabase connection successful!")
        print(f"📊 Found {len(response.data)} projects in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


async def main():
    """Main setup function"""
    print("🚀 Starting OAuth database setup...")
    
    # Test Supabase connection
    if not test_supabase_connection():
        print("❌ Please check your Supabase credentials and try again")
        return
    
    # Setup OAuth tables
    success = await setup_oauth_tables()
    
    if success:
        print("\n🎉 OAuth setup completed!")
        print("\n📋 Next steps:")
        print("1. 🌐 Configure OAuth providers in Supabase Dashboard")
        print("2. 🔧 Update your .env file with OAuth credentials")
        print("3. 🚀 Start your FastAPI server")
        print("4. 🧪 Test OAuth login from your frontend")
        print("\n📖 See docs/oauth-setup-guide.md for detailed instructions")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")


if __name__ == "__main__":
    asyncio.run(main())
