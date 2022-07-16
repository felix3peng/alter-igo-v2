from flask import Blueprint
from flask import current_app as app

landing_bp = Blueprint(
    'landing', __name__,
    template_folder='templates',
    static_folder='static'
)