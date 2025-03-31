from app import create_app, db
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application - explicitly for Gunicorn to find
logger.info("Creating Flask application in app.py")
app = create_app()

# Initialize database within app context
with app.app_context():
    try:
        # Create tables that might not be covered by migrations
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

if __name__ == "__main__":
    # For manual/local running: python app.py
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 