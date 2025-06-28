import subprocess
import sys
import os

def check_python_version():
    major, minor, _ = sys.version_info
    if major == 3 and minor >= 11 and minor <= 13:
        print(f"Python {major}.{minor} is supported ✓")
        return True
    else:
        print(f"ERROR: Python {major}.{minor} is not supported!")
        print("This application requires Python 3.11, 3.12, or 3.13")
        return False

def check_dependencies():
    try:
        import flask
        import werkzeug
        import sqlalchemy
        import flask_login
        import flask_migrate
        print("All core dependencies are installed ✓")
        return True
    except ImportError as e:
        print(f"ERROR: Missing dependency - {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_database():
    try:
        subprocess.run([sys.executable, "reset_migrations.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Database setup failed!")
        return False

def main():
    print("=== Project Management System Deployment ===")
    
    if not check_python_version() or not check_dependencies():
        return
    
    print("\nSetting up database...")
    if not setup_database():
        return
    
    print("\nStarting application...")
    subprocess.run([sys.executable, "run.py"])

if __name__ == "__main__":
    main()
