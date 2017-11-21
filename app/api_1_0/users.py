# -*- coding: utf-8 -*-
from . import api
from .utils import *

@api.route('/users')
def user():
    return "This is a user."

@api.route('/users/<int:id>')
def get_user(id):
    """
    @api {get} /users/:id Get an user
    @apiVersion 1.0.0
    @apiName get_user
    @apiGroup User

    @apiDescription Get an user for given id.

    @apiParam {Number} id The user's id.

    @apiSuccessExample {json} Success Result:
    HTTP/1.1 200 OK
    {
        "data": {
            "id": 4812,
            "username": "MIC"
        },
        "status": {
            "code": 200,
            "message": "Ok all right."
        }
    }
    @apiErrorExample {json} Error Result:
    HTTP/1.1 404 Not Found
    {
        "status": {
            "code": 404,
            "message": "No result match."
        }
    }
    """
    return status_response(R200_OK)

@api.route('/users/<int:id>', methods=['POST'])
def update_user(id):
    """
    @api {post} /users/:id Update an user
    @apiVersion 1.0.0
    @apiName update_user
    @apiGroup User

    @apiParam {Number} id  The user's id.
    @apiParam {String} first_name  The first name of the user.
    @apiParam {String} last_name  The last name of the user.

    @apiSuccessExample {json} Success Result:
    HTTP/1.1 200 OK
    {
        "status": {
            "code": 201,
            "message": "All created."
        }
    }
    """
    pass