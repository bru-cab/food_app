import logging
from app import create_app, db
from flask_migrate import upgrade

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_db():
    """Set up the database with proper application context"""
    try:
        logger.info("Starting database setup process")
        app = create_app()
        with app.app_context():
            # Run migrations
            logger.info("Running database migrations")
            upgrade()
            
            # Create any tables not handled by migrations
            logger.info("Creating any remaining tables")
            db.create_all()
            
            logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    setup_db() 