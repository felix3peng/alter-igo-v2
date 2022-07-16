from flask import Blueprint
from flask import current_app as app

help_bp = Blueprint(
    'help', __name__,
    template_folder='templates',
    static_folder='static'
)