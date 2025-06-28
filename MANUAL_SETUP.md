# Manual Installation Guide for Project Management System

This guide will walk you through the step-by-step manual installation of the Project Management System without using scripts.

## Prerequisites

- Python 3.11 or 3.12 (recommended)
- Text editor (such as Visual Studio Code, Notepad++, etc.)
- Command line/terminal access
- Git (optional, for version control)

## Step 1: Install Python

1. Download Python 3.11.8 from the official website: https://www.python.org/downloads/release/python-3118/
2. Run the installer
3. **Important**: Check the box that says "Add Python to PATH" during installation
4. Complete the installation
5. Open a command prompt/terminal and verify the installation by typing:
   ```
   python --version
   ```
   You should see "Python 3.11.8" or similar output.

## Step 2: Create a Virtual Environment

1. Navigate to your project directory:
   ```
   cd e:\apps\new\New folder (4)\project_management
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows**:
     ```
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```
     source venv/bin/activate
     ```

   You should now see `(venv)` at the beginning of your command prompt, indicating the virtual environment is active.

## Step 3: Install Required Packages

1. With the virtual environment activated, install all required packages:
   ```
   pip install Flask==2.3.3
   pip install Werkzeug==2.3.7
   pip install Flask-SQLAlchemy==3.1.1
   pip install Flask-Login==0.6.2
   pip install Flask-WTF==1.2.1
   pip install Flask-Migrate==4.0.5
   pip install SQLAlchemy==2.0.26
   pip install email-validator==2.1.0
   pip install python-dotenv==1.0.0
   pip install Jinja2==3.1.3
   pip install itsdangerous==2.1.2
   pip install Flask-Bcrypt==1.0.1
   pip install Pillow==10.2.0
   pip install Flask-Mail==0.9.1
   pip install pyjwt==2.8.0
   pip install python-dateutil==2.8.2
   pip install pytz==2023.3
   pip install gunicorn==21.2.0
   pip install alembic==1.13.1
   ```

   Alternatively, you can install all packages at once from the requirements.txt file:
   ```
   pip install -r requirements.txt
   ```

## Step 4: Set Up Environment Variables

1. Create a file named `.env` in the root project directory using your text editor
2. Add the following content to the file:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-replace-this-in-production
   DATABASE_URL=sqlite:///site.db
   ```

## Step 5: Initialize the Database

1. Ensure your virtual environment is activated, then run:
   ```
   flask db init
   ```

2. Create the initial migration:
   ```
   flask db migrate -m "Initial database setup"
   ```

3. Apply the migration to create the database:
   ```
   flask db upgrade
   ```

## Step 6: Create Admin User (Optional)

You can create an admin user by opening a Python REPL in the project context:

1. Make sure your virtual environment is activated
2. Start the Python interpreter:
   ```
   python
   ```

3. Execute the following Python code:
   ```python
   from app import create_app, db
   from app.models import User, UserRole
   from werkzeug.security import generate_password_hash
   
   app = create_app()
   with app.app_context():
       admin = User(
           username='admin',
           email='admin@example.com',
           password=generate_password_hash('admin123'),
           role=UserRole.ADMIN
       )
       db.session.add(admin)
       db.session.commit()
       print("Admin user created successfully!")
   ```

4. Exit the Python interpreter:
   ```
   exit()
   ```

## Step 7: Run the Application

1. With your virtual environment still activated, run:
   ```
   python run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

3. You should see the application login page. If you created an admin user, you can log in using:
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

- **Python not found**: Ensure Python is installed and added to your PATH
- **Module not found errors**: Make sure you've installed all required packages and your virtual environment is activated
- **Database errors**: Check that the database migrations were applied successfully
- **Port already in use**: If port 5000 is already in use, you can modify the port in `run.py`

## Manual Database Reset

If you need to completely reset the database:

1. Delete the SQLite database file:
   - Windows: `del instance\site.db`
   - macOS/Linux: `rm instance/site.db`
2. Delete the migrations folder:
   - Windows: `rmdir /s /q migrations`
   - macOS/Linux: `rm -rf migrations`
3. Follow steps 5-6 above to recreate the database
