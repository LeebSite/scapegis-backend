#!/usr/bin/env python3
"""
Universal server startup script for ScapeGIS Backend
Works on Windows, macOS, and Linux
"""
import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_virtual_environment():
    """Check if virtual environment is activated"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated")
        return True
    else:
        print("⚠️  Virtual environment not detected")
        return False

def install_dependencies():
    """Install dependencies if needed"""
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencies already installed")
    except ImportError:
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def check_environment_file():
    """Check if .env file exists"""
    if os.path.exists('.env'):
        print("✅ Environment file (.env) found")
        return True
    elif os.path.exists('.env.example'):
        print("⚠️  .env file not found, but .env.example exists")
        print("💡 Copy .env.example to .env and configure your settings")
        return False
    else:
        print("❌ No environment configuration found")
        return False

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting ScapeGIS Backend Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔧 OAuth Google: http://localhost:8001/api/v1/auth/oauth/google")
    print("\n⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8001", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    print("🌍 ScapeGIS Backend Server Startup")
    print("=" * 40)
    
    # System checks
    check_python_version()
    
    # Virtual environment check
    if not check_virtual_environment():
        print("\n💡 Recommendation: Use virtual environment")
        print("   python -m venv venv")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print()
    
    # Environment file check
    if not check_environment_file():
        print("\n❌ Please configure your environment file first")
        return
    
    # Install dependencies
    install_dependencies()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
