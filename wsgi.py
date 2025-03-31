import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import create_app, db
from flask_migrate import upgrade

# Create the Flask application
logger.info("Creating Flask application")
application = create_app()

# For backwards compatibility
app = application

# Run within application context
with application.app_context():
    logger.info("Running database migrations")
    # Run migrations
    upgrade()
    logger.info("Creating database tables")
    # Initialize database tables
    db.create_all()

if __name__ == "__main__":
    logger.info("Running application")
    application.run() 