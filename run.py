import os
import sys
from app import create_app, db
from flask_migrate import Migrate
from app.models import User, UserRole
from werkzeug.security import generate_password_hash

# Ensure the instance directory exists
if not os.path.exists('instance'):
    os.makedirs('instance')

app = create_app()
migrate = Migrate(app, db)

def init_db():
    """Initialize the database if needed"""
    with app.app_context():
        try:
            db.create_all()  # Ensure all tables are created
            if User.query.filter_by(username='admin').first() is None:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('admin123'),
                    role=UserRole.ADMIN.value,
                    fs_uniquifier=os.urandom(16).hex()  # Add this for Flask-Security
                )
                db.session.add(admin)
                db.session.commit()
                print("Created default admin user: admin/admin123")
        except Exception as e:
            print(f"Error initializing database: {e}")
            print("Ensure the database is correctly configured in .env")

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'UserRole': UserRole}

if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode
