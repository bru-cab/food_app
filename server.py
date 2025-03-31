from app import create_app, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Creating Flask application in server.py")
# Create application instance
flask_app = create_app()

# Initialize database within app context
with flask_app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully in server.py")
    except Exception as e:
        logger.error(f"Error creating database tables in server.py: {e}")

# For Gunicorn to find (both names commonly used)
app = flask_app
application = flask_app

if __name__ == "__main__":
    # For running locally with: python server.py
    app.run(host="0.0.0.0", port=8080) 