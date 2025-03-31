from app import create_app, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info("Initializing application in wsgi.py")
    
    # For Gunicorn
    application = create_app()
    
    # Initialize database within app context
    with application.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully in wsgi.py")
        except Exception as e:
            logger.error(f"Error creating database tables in wsgi.py: {e}")
    
    # For compatibility 
    app = application
    
    logger.info("Application initialized successfully in wsgi.py")
except Exception as e:
    logger.error(f"Error initializing application in wsgi.py: {e}")
    raise

if __name__ == "__main__":
    app.run() 