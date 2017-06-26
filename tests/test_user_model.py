#!venv/bin/python
# -*- coding: utf-8 -*-
import unittest

from app import create_app, db
from app.models import User

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_avatar(self):
        u = User(username='john',
                 email='john@example.com',
                 password='Mic45x67',
                 time_zone='zh')
        avatar = u.g_avatar(128)
        expected = 'http://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6'
        assert avatar[0:len(expected)] == expected

    def test_make_unique_username(self):
        u = User(username='john',
                 email='john@example.com',
                 password='Mic45x67',
                 time_zone='zh')
        db.session.add(u)
        db.session.commit()

        username = User.make_unique_username('john')
        assert username != 'john'

        u = User(username=username,
                 email='susan@example.com',
                 password='Mic45x67',
                 time_zone='zh')
        db.session.add(u)
        db.session.commit()

        username2 = User.make_unique_username('john')
        assert username2 != 'john'
        assert username2 != username


if __name__ == '__main__':
    unittest.main()
