from flask import Blueprint, render_template
from flask import current_app as app

# blueprint configuration for landing page
docs_bp = Blueprint(
    'docs', __name__,
    template_folder='templates',
    static_folder='static'
)


# create base route for landing page
@docs_bp.route('/')
def landing():
    return render_template('landing.html',
    title='Alter Igo: Welcome',
    subtitle='Log in to access Alter Igo',
    template='landing-template')
