# -*- coding: utf-8 -*-
from flask import jsonify, g

from .. import db
from .auth import auth
from .errors import forbidden, unauthorized
from .utils import full_response, R200_OK
from . import api


@api.route('/token', methods=['POST'])
@auth.login_required
def get_token():
    """
    Request a user token.
    This endpoint is requires basic auth with email and password.
    """
    expired_time = 7200
    token = g.current_user.generate_auth_token(expiration=expired_time)
    
    return full_response(R200_OK, {
        'token': token,
        'expiration': expired_time
    })


@api.route('/tokens', methods=['DELETE'])
@auth.login_required
def revoke_token():
    """
    Revoke a user token.
    This endpoint is requires a valid user token.
    """
    
    return '', 204