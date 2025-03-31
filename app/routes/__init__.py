# Routes package 
from app.routes.auth import auth_bp, login_required
from app.routes.main import main_bp
from app.routes.api import api_bp

__all__ = ['auth_bp', 'main_bp', 'api_bp', 'login_required'] 