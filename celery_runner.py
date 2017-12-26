# -*- coding: utf-8 -*-
import os

from celery import Celery

from app import create_app

# 加载环境变量
if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

def make_celery(app):
    """Create the celery process."""

    # Init the celery object via app's configuration
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'])

    # Flask-Celery-Helper to auto-setup the config.
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            """Will be execute when create the instance object of ContextTask."""

            # Will context(Flask's Extends) of app object(Producer Sit)
            # be included in celery object(Consumer Site).
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    # Include the app_context into celery.Task.
    # Let other Flask extensions can be normal calls.
    celery.Task = ContextTask
    return celery

flask_app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
# 1. Each celery process needs to create an instance of the Flask application.
# 2. Register the celery object into the app object.
celery = make_celery(flask_app)
