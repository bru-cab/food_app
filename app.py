from app import create_app
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application - explicitly for Gunicorn to find
logger.info("Creating Flask application in app.py")
app = create_app()

if __name__ == "__main__":
    # For manual/local running: python app.py
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 