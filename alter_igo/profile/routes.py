from flask import Blueprint
from flask import current_app as app

profile_bp = Blueprint(
    'profile', __name__,
    template_folder='templates',
    static_folder='static'
)