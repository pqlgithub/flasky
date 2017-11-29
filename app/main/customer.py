# -*- coding: utf-8 -*-
from flask import g, render_template, redirect, url_for, abort, flash, request,\
    current_app
from flask_login import login_required, current_user
from flask_babelex import gettext
from . import main
from .. import db
from app.models import Client, ClientStatus
from app.forms import ClientForm
from ..utils import Master, custom_response, make_unique_key, make_pw_hash
from ..decorators import user_has

