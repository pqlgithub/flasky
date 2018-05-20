# -*- coding: utf-8 -*-
import json
import time

from flask import render_template, redirect, request, url_for, flash, abort, \
    make_response, session
from flask_login import login_user, logout_user, login_required, \
    current_user
from flask_babelex import gettext
from . import auth
from .. import db
from app.models import User, UserIdType
from .forms import LoginForm, SignupForm, ResetPasswordFrom, LoginErrorForm
from ..email import send_email
from ..yunpian import send_phoneverifycode
from app.utils import next_is_valid, make_verifycode_img
from app.tasks import build_default_setting


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    login_count = session.get('user_ip')

    if not login_count:
        login_count = 0
        session['user_ip'] = 0

    if login_count < 2:
        form = LoginForm()
        status = 'login'
    else:
        form = LoginErrorForm()
        status = 'loginerror'

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            del session['user_ip']
            if session.get('start_time'):
                del session['start_time']

            # 商家入口，消费者不能登录
            if user.id_type == UserIdType.BUYER:
                abort(401)

            login_user(user, form.remember_me.data)
            next_url = request.args.get('next')
            if not next_is_valid(next_url):
                abort(400)

            default_index = url_for('main.index')
            if user.id_type == UserIdType.CUSTOMER:  # 跳转分销商后台
                default_index = url_for('distribute.index')

            return redirect(next_url or default_index)

        flash(gettext('Account or Password is Error!'), 'danger')
        session['user_ip'] += 1

    # 如已登录，则自动跳转
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    return render_template('auth/login.html',
                           form=form,
                           status=status)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    """用户注册"""
    form = SignupForm()
    if form.validate_on_submit():
        if session.get('start_time'):
            del session['start_time']
        user = User()

        user.areacode = form.areacode.data
        user.email = form.email.data
        user.username = form.email.data
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


@auth.route('/reset_password',methods=['GET','POST'])
def reset_password():
    """重设密码"""
    form = ResetPasswordFrom()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter(User.email==email).first()
        user.password = password

        db.session.add(user)

        db.session.commit()

        return redirect(url_for('main.index'))

    return render_template('auth/reset_password.html',
                           form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
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


@auth.route('/forbidden')
def forbidden():
    """拒绝访问"""
    errmsg = '权限限制，不允许访问！'

    return render_template('auth/forbidden.html', errmsg=errmsg)


@auth.route('/get_verifycode_img')
def get_verifycode_img():
    """获取验证码图片"""

    verifycode, data = make_verifycode_img()
    print(verifycode)

    # 将验证码存放在session里
    session["verifycode"]=verifycode

    return make_response(data)

@auth.route('/get_phoneverifycode',methods=['GET','POST'])
def get_phoneverifycode():
    """获取手机验证码"""
    # 用户手机号
    phonenum = request.form.get('phonenum')

    if not phonenum:
        flash(gettext('请输入手机号。'), 'danger')
        return json.dumps({'status': 0})

    # 地区编码
    areacode = request.form.get('areacode')
    page = request.form.get('page')
    username = User.query.filter(User.email == phonenum).first()

    start_time = session.get('start_time')
    # 时间间隔判断
    if not start_time:
        session['start_time'] = time.time()
        msg = send_phoneverifycode(phonenum, areacode, page, username)
        return json.dumps(msg)

    else:

        current_time = time.time()
        time_interval = current_time - start_time  # 时间间隔
        if time_interval >= 60:
            msg = send_phoneverifycode(phonenum, areacode, page, username)
            return json.dumps(msg)

        else:
            flash(gettext('({int(60-time_interval)}s)后获取验证码。'), 'danger')
            return json.dumps({'status': 0})
