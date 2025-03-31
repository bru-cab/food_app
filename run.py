import os
import logging
from app import create_app, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app - this is what Gunicorn will import 
app = create_app()

# This is only used when running directly
if __name__ == "__main__":
    # Initialize with app context for local development
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
    
    # Run the app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 