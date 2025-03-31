import logging
import os
from app import create_app, db
from flask_migrate import upgrade, Migrate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_db():
    """Set up the database with proper application context"""
    try:
        logger.info("Starting database setup process")
        
        # Get DATABASE_URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not found in environment")
        else:
            logger.info(f"Using database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
        
        # Create app with explicit app context
        app = create_app()
        
        # Ensure migrations are properly initialized
        migrate = Migrate(app, db)
        
        with app.app_context():
            logger.info("Running database migrations")
            try:
                upgrade()
                logger.info("Migrations completed successfully")
            except Exception as e:
                logger.error(f"Migration error: {e}")
                
            logger.info("Creating any remaining tables")
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Error creating tables: {e}")
                
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    setup_db() 