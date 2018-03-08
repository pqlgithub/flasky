# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, current_app
from flask_babelex import gettext

from . import adminlte
from .. import db, cache
from app.models import WxTemplate, WxToken
from app.forms import WxTemplateForm
from app.helpers import WxApp, WxAppError
from app.utils import custom_response, timestamp


def load_common_data():
    """
    私有方法，装载共用数据
    """
    return {
        'top_menu': 'weixin',
    }


@adminlte.route('/weixin/settings')
def setting_weixin():
    """配置微信第三方平台相关参数"""
    return render_template('adminlte/weixin/get_token.html',
                           **load_common_data())


@adminlte.route('/weixin/init_token')
def get_weixin_token():
    """初始化微信第三方平台component_access_token"""
    component_app_id = current_app.config['WX_APP_ID']
    is_exist = False
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    if wx_token:
        # 检测是否过期
        now_time = int(timestamp())
        if wx_token.created_at + wx_token.expires_in - 600 > now_time:
            return custom_response(True, 'Component access token not expired!')
        is_exist = True

    component_verify_ticket = cache.get('wx_component_verify_ticket')
    if component_verify_ticket is None:
        return custom_response(True, "Component verify ticket isn't exist!!!")

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'])

        result = wx_app_api.get_component_token(component_verify_ticket)

        if is_exist:
            wx_token.access_token = result.component_access_token
            wx_token.expires_in = result.expires_in
            wx_token.created_at = int(timestamp())
        else:
            # 更新数据
            wx_token = WxToken(
                app_id=current_app.config['WX_APP_ID'],
                access_token=result.component_access_token,
                expires_in=result.expires_in
            )
            db.session.add(wx_token)

        db.session.commit()
    except WxAppError as err:
        current_app.logger.warn('Request weixin access token error: %s' % err)
        return custom_response(False, 'Request access token error: {}'.format(err))

    flash('刷新微信Access Token成功！', 'success')

    return redirect(url_for('.setting_weixin'))


@adminlte.route('/templates')
@adminlte.route('/templates/<int:page>')
def show_templates(page=1):
    """小程序模板管理"""
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 0, type=int)

    if not status:
        query = WxTemplate.query
    else:
        query = WxTemplate.query.filter_by(status=status)

    paginated_templates = query.order_by(WxTemplate.created_at.desc()).paginate(page, per_page)

    return render_template('adminlte/weixin/show_list.html',
                           paginated_templates=paginated_templates,
                           status=status,
                           sub_menu='templates',
                           **load_common_data())


@adminlte.route('/templates/create', methods=['GET', 'POST'])
def create_template():
    """添加模板"""
    form = WxTemplateForm()
    if form.validate_on_submit():
        wx_template = WxTemplate(
            template_id=form.template_id.data,
            name=form.name.data,
            description=form.description.data,
            cover_id=form.cover_id.data,
            attachment=form.attachment.data,
            status=form.status.data
        )
        db.session.add(wx_template)
        db.session.commit()

        flash(gettext('Add wx_template is ok!'), 'success')

        return redirect(url_for('.show_templates'))

    mode = 'create'
    return render_template('adminlte/weixin/create_and_edit.html',
                           form=form,
                           mode=mode,
                           sub_menu='templates',
                           **load_common_data())


@adminlte.route('/templates/<int:rid>/edit', methods=['GET', 'POST'])
def edit_template(rid):
    """编辑模板"""
    wx_template = WxTemplate.query.get_or_404(rid)

    form = WxTemplateForm()
    if form.validate_on_submit():
        form.populate_obj(wx_template)

        db.session.commit()

        flash(gettext('Update wx_template is ok!'), 'success')

        return redirect(url_for('.show_templates'))

    mode = 'edit'
    form.template_id.data = wx_template.template_id
    form.name.data = wx_template.name
    form.description.data = wx_template.description
    form.cover_id.data = wx_template.cover_id
    form.attachment.data = wx_template.attachment
    form.status.data = wx_template.status

    return render_template('adminlte/weixin/create_and_edit.html',
                           form=form,
                           mode=mode,
                           template=wx_template,
                           sub_menu='templates',
                           **load_common_data())


@adminlte.route('/templates/delete', methods=['POST'])
def delete_template():
    """禁用模板"""
    selected_ids = request.form.getlist('selected[]')
    if not selected_ids or selected_ids is None:
        flash('Disabled template is null!', 'danger')
        abort(404)

    for rid in selected_ids:
        wx_template = WxTemplate.query.get_or_404(int(rid))
        wx_template.mark_set_disabled()

    db.session.commit()

    flash('Disabled wx_template is ok!', 'success')

    return redirect(url_for('.show_templates'))
