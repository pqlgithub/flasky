# -*- coding: utf-8 -*-
from flask import current_app
from app.extensions import fsk_celery


@fsk_celery.task(name='demo.add_together')
def add_together(x, y):
    current_app.logger.debug('run task add_together.')
    return x + y
