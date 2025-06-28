"""
Simplified starter script for the Project Management System
This script checks the environment, fixes common issues, and runs the application
"""
import os
import sys
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_environment():
    """Run the environment check script"""
    logger.info("Checking environment...")
    try:
        subprocess.run([sys.executable, 'fix_environment.py'], check=True)
        return True
    except subprocess.CalledProcessError:
        logger.error("Environment check failed.")
        return False

def setup_database():
    """Initialize the database"""
    logger.info("Setting up database...")
    try:
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            logger.info("Initializing migrations...")
            subprocess.run([sys.executable, '-m', 'flask', 'db', 'init'], check=True)
        
        # Create initial migration if not exists
        logger.info("Creating migration...")
        subprocess.run(
            [sys.executable, '-m', 'flask', 'db', 'migrate', '-m', 'Initial migration'],
            check=True
        )
        
        # Apply migrations
        logger.info("Applying migrations...")
        subprocess.run([sys.executable, '-m', 'flask', 'db', 'upgrade'], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Database setup failed: {e}")
        return False

def run_application():
    """Run the Flask application"""
    logger.info("Starting application...")
    try:
        # Run the application
        os.environ['FLASK_APP'] = 'run.py'
        os.environ['FLASK_ENV'] = 'development'
        subprocess.run([sys.executable, 'run.py'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Application failed to start: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
        return True

def main():
    """Main function that runs all steps"""
    logger.info("Starting Project Management System...")
    
    # Step 1: Check environment
    if not check_environment():
        logger.error("Environment check failed. Please fix the issues and try again.")
        return False
    
    # Step 2: Setup database
    if not setup_database():
        logger.error("Database setup failed. Please fix the issues and try again.")
        return False
    
    # Step 3: Run application
    if not run_application():
        logger.error("Application failed to start. Please fix the issues and try again.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
