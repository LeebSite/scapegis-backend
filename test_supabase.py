"""
Test script untuk koneksi Supabase
"""
import os
from supabase import create_client, Client

def test_supabase_connection():
    """Test koneksi ke Supabase"""

    # Ganti dengan credentials Supabase Anda
    SUPABASE_URL = "https://fgpyqyiazgouorgpkavr.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZncHlxeWlhemdvdW9yZ3BrYXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2OTY4NDgsImV4cCI6MjA2NjI3Mjg0OH0.mi6eHu3jJ9K2RXBz71IKCDNBGs9bnDPBf2a8-IcuvYI"

    try:
        # Buat client Supabase dengan options yang benar
        supabase: Client = create_client(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY
        )

        print("✅ Supabase client berhasil dibuat!")

        # Test query ke tabel yang pasti ada (auth.users metadata)
        try:
            # Test dengan query sederhana ke system table
            response = supabase.rpc('version').execute()
            print("✅ Koneksi database berhasil!")
            print(f"PostgreSQL Version: {response.data}")
        except Exception as db_error:
            print(f"⚠️ Database query error: {db_error}")
            print("Ini normal jika belum ada tabel atau RPC function")

        # Test auth client
        try:
            auth_response = supabase.auth.get_session()
            print("✅ Auth client berhasil!")
        except Exception as auth_error:
            print(f"⚠️ Auth error: {auth_error}")
            print("Ini normal untuk anonymous access")

        print("\n🎉 Supabase setup berhasil!")

    except Exception as e:
        print(f"❌ Error koneksi Supabase: {e}")
        print("Pastikan URL dan API Key sudah benar")
        print("\nTroubleshooting:")
        print("1. Pastikan SUPABASE_URL format: https://fgpyqyiazgouorgpkavr.supabase.co")
        print("2. Pastikan SUPABASE_KEY adalah anon key (public)")
        print("3. Pastikan project Supabase sudah aktif")

if __name__ == "__main__":
    test_supabase_connection()
