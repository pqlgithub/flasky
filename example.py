# -*- coding: utf-8 -*-
from flask import Flask
from flask_celery import Celery

app = Flask('example')
app.config['CELERY_BROKER_URL'] = 'redis://:Fr%bird@201403$01@localhost:6379/5'
app.config['CELERY_RESULT_BACKEND'] = 'redis://:Fr%bird@201403$01@localhost:6379/6'
celery = Celery(app)

@celery.task()
def add_together(a, b):
    return a + b

if __name__ == '__main__':
    result = add_together.delay(23, 42)
    print(result.get())