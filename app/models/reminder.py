# -*- coding: utf-8 -*-
from sqlalchemy import event
from app import db
#from app.tasks import on_reminder_save

__all__ = [
    'Reminder'
]


class Reminder(db.Model):
    """Represents Protected reminders."""

    __tablename__ = 'reminders'

    id = db.Column(db.String(45), primary_key=True)
    date = db.Column(db.DateTime())
    email = db.Column(db.String(255))
    text = db.Column(db.Text())

    def __init__(self, id, text):
        self.id = id
        self.email = text

    def __repr__(self):
        return '<Reminder `{}`>'.format(self.text[:20])

# Will be callback on_reminder_save when insert recond into table `reminder`.
#event.listen(Reminder, 'after_insert', on_reminder_save)