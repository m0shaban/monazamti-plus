from app import create_app, db
from app.models import User, UserRole
from werkzeug.security import generate_password_hash

app = create_app()

def init_db():
    with app.app_context():
        try:
            # Drop and recreate all tables
            db.drop_all()
            db.create_all()
            
            # Create admin user if doesn't exist
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password=generate_password_hash('admin123', method='sha256'),
                    role=UserRole.ADMIN
                )
                db.session.add(admin)
                db.session.commit()
                print("Default admin created successfully")
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

if __name__ == '__main__':
    if init_db():
        app.run(debug=True)
    else:
        print("Failed to initialize database. Please check the error and try again.")
