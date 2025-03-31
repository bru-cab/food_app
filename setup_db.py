from app import create_app, db, init_db
from flask_migrate import upgrade

def setup_db():
    """Set up the database with proper application context"""
    app = create_app()
    with app.app_context():
        # Run migrations
        upgrade()
        # Create any tables not handled by migrations
        db.create_all()
        print("Database setup completed successfully")

if __name__ == "__main__":
    setup_db() 