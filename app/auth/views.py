# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, \
    current_user
from flask_babelex import gettext
from . import auth
from .. import db
from app.models import User, UserIdType
from .forms import LoginForm, SignupForm
from ..email import send_email
from app.utils import next_is_valid
from app.tasks import build_default_setting


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next_url = request.args.get('next')
            if not next_is_valid(next_url):
                abort(400)

            return redirect(next_url or url_for('main.index'))

        flash(gettext('Account or Password is Error!'), 'danger')

    # 如已登录，则自动跳转
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    return render_template('auth/login.html',
                           form=form)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """用户注册"""
    form = SignupForm()
    if form.validate_on_submit():
        user = User()

        user.email = form.email.data
        user.username = form.username.data
        user.password = form.password.data
        user.id_type = UserIdType.SUPPLIER
        user.time_zone = 'zh'

        db.session.add(user)

        db.session.commit()

        # Send confirm.txt email
        # token = user.generate_confirmation_token()
        # send_email(user.email, 'Confirm Your Account',
        #           'auth/email/confirm', user=user, token=token)

        # 触发任务
        build_default_setting.apply_async(args=[user.id])

        return redirect(url_for('main.index'))

    return render_template('auth/signup.html',
                           form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


@auth.route('/confirm/<token>', methods=['GET'])
@login_required
def confirm(token):
    """确认用户账户"""
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.', 'danger')

    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    """重新发送账户确认邮件"""
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)

    flash('A new confirmation email has been sent to you by email.', 'danger')

    return redirect(url_for('main.index'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))

    return render_template('auth/unconfirmed.html',
                           token=current_user.generate_confirmation_token())
