# -*- coding: utf-8 -*-
from flask_assets import Environment, Bundle


# Create the Flask-Assets instance
assets_env = Environment()

bundles = {
    'admin_js' : Bundle(
        'js/jquery.min.js',
        'js/bootstrap.min.js',
        'js/jquery.cookie.js',
        'js/sweet-alert.min.js',
        'js/select2.js',
        'js/plupload.full.min.js',
        'js/jquery.plupload.queue.js',
        output='dist/admin.js'
    ),
    'app_js': Bundle(
        'js/app.js',
        filters='jsmin',
        output='dist/app.js'
    )
}
