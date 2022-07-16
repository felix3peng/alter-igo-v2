# compile static assets
from flask import current_app as app
from flask_assets import Bundle


# define function to call for building static assets
def compile_static_assets(assets):
    assets.auto_build = True
    assets.debug = False
    common_style_bundle = Bundle(
        'src/less/*.less',
        filters='less,cssmin',
        output='dist/css/style.css',
        extra={'rel': 'stylesheet/less'}
    )

    landing_style_bundle = Bundle(
        'landing_bp/less/landing.less',
        filters='less,cssmin',
        output='dist/css/landing.css',
        extra={'rel': 'stylesheet/less'}
    )

    profile_style_bundle = Bundle(
        'profile_bp/less/profile.less',
        filters='less,cssmin',
        output='dist/css/profile.css',
        extra={'rel': 'stylesheet/less'}
    )

    home_style_bundle = Bundle(
        'home_bp/less/home.less',
        filters='less,cssmin',
        output='dist/css/home.css',
        extra={'rel': 'stylesheet/less'}
    )

    help_style_bundle = Bundle(
        'help_bp/less/help.less',
        filters='less,cssmin',
        output='dist/css/help.css',
        extra={'rel': 'stylesheet/less'}
    )
    
    docs_style_bundle = Bundle(
        'docs_bp/less/docs.less',
        filters='less,cssmin',
        output='dist/css/docs.css',
        extra={'rel': 'stylesheet/less'}
    )

    assets.register('common_style_bundle', common_style_bundle)
    assets.register('landing_style_bundle', landing_style_bundle)
    assets.register('profile_style_bundle', profile_style_bundle)
    assets.register('home_style_bundle', home_style_bundle)
    assets.register('help_style_bundle', help_style_bundle)
    assets.register('docs_style_bundle', docs_style_bundle)

    if app.config["FLASK_ENV"] == "development":
        common_style_bundle.build()
        landing_style_bundle.build()
        profile_style_bundle.build()
        home_style_bundle.build()
        help_style_bundle.build()
        docs_style_bundle.build()

    return assets
