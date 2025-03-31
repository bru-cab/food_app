from flask import Blueprint, render_template
from app.models.user import User
from app.routes.auth import login_required
from flask import session
import logging

logger = logging.getLogger(__name__)

# Create a blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    current_user = User.query.get(session['user_id'])
    return render_template('index.html', current_user=current_user) 