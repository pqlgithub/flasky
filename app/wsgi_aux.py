# -*- coding: utf-8 -*-
import os

from . import create_app

# Create an application instance that auxiliary processes such as Celery
# workers can use
app = create_app(os.environ.get('FLASK_CONFIG', 'default'))
