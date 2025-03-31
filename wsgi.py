import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app import create_app

# Create the Flask application
logger.info("Creating Flask application object (wsgi.py)")
application = create_app()

# For potential backwards compatibility or direct runs, although not recommended for prod
app = application

if __name__ == "__main__":
    # This block is primarily for local development testing (e.g., python wsgi.py)
    # Database setup should ideally be handled by migrations run via Procfile or manually
    logger.info("Running application directly via wsgi.py (likely local dev)")
    # Avoid running db setup here in production deployments
    # with application.app_context():
    #     from flask_migrate import upgrade
    #     logger.info("Running database migrations (direct run)")
    #     upgrade()
    #     logger.info("Creating database tables (direct run)")
    #     db.create_all() # Ensure db is imported if uncommented
    application.run() # Consider adding host='0.0.0.0' if needed for local network access 