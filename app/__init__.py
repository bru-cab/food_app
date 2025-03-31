from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
import sys
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    logger.info("Starting create_app function in app/__init__.py")
    
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    logger.info("Flask app instance created")
    
    app.config.from_object(config_class)
    logger.info("Config loaded")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    logger.info("Database extensions initialized")
    
    # Initialize OpenAI if API key is available
    if config_class.OPENAI_API_KEY:
        import openai
        openai.api_key = config_class.OPENAI_API_KEY
        logger.info("OpenAI initialized")
    
    # Register blueprints
    with app.app_context():
        logger.info("Importing route blueprints")
        from app.routes import auth_bp, main_bp, api_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("Blueprints registered")
    
    # Serve static files
    @app.route('/static/<path:path>')
    def send_static(path):
        from flask import send_from_directory
        return send_from_directory('../static', path)
    
    # Log successful app creation
    logger.info("App created successfully")
    
    return app 