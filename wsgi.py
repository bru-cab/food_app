from app import create_app, db
from flask_migrate import upgrade

# Create the Flask application
application = create_app()

# For backwards compatibility
app = application

# Run within application context
with application.app_context():
    # Run migrations
    upgrade()
    # Initialize database tables
    db.create_all()

if __name__ == "__main__":
    application.run() 