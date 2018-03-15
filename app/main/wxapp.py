# -*- coding: utf-8 -*-
import json
from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from sqlalchemy.sql import func
from . import main
from .. import db, cache
from app.models import WxToken, WxMiniApp, Store, WxTemplate, WxPayment, WxAuthorizer, Client, WxServiceMessage, \
    WxVersion
from app.helpers import WxApp, WxAppError, WxaOpen3rd, gen_3rd_session_key
from app.tasks import bind_wxa_tester, unbind_wxa_tester, create_banner_spot, create_wxapi_appkey, reply_wxa_service
from app.forms import WxReplyForm
from ..utils import Master, timestamp, status_response, full_response, R200_OK, make_unique_key, custom_response


@main.route('/wxapps')
def wxapps():
    """小程序列表"""
    mini_apps = WxMiniApp.query.filter_by(master_uid=Master.master_uid()).all()

    return render_template('wxapp/index.html',
                           mini_apps=mini_apps)


@main.route('/wxapps/setting', methods=['GET', 'POST'])
def wxapp_setting():
    """配置小程序参数"""
    auth_app_id = request.values.get('auth_app_id')
    is_auth = False
    if not auth_app_id:
        return redirect(url_for('.wxapps'))

    # 根据auth_app_id获取auth access token
    wx_mini_app = WxMiniApp.query.filter_by(auth_app_id=auth_app_id).first()
    if wx_mini_app is None:
        # 获取小程序信息
        try:
            result = _get_authorizer_info(auth_app_id)
        except WxAppError as err:
            flash('小程序获取信息失败：%s，请重试！' % err, 'danger')
            return render_template('wxapp/index.html', auth_status=is_auth)

        current_app.logger.debug('Authorizer result %s' % result)

        authorizer_info = result.authorizer_info
        authorization_info = result.authorization_info
        try:
            # 新增
            new_serial_no = WxMiniApp.make_unique_serial_no()
            wx_mini_app = WxMiniApp(
                master_uid=Master.master_uid(),
                serial_no=new_serial_no,
                auth_app_id=auth_app_id,
                nick_name=authorizer_info.nick_name,
                head_img=authorizer_info.head_img,
                signature=authorizer_info.signature,
                user_name=authorizer_info.user_name,
                principal_name=authorizer_info.principal_name,
                service_type_info=json.dumps(authorizer_info.service_type_info),
                verify_type_info=json.dumps(authorizer_info.verify_type_info),
                business_info=json.dumps(authorizer_info.business_info),
                qrcode_url=authorizer_info.qrcode_url,
                mini_program_info=json.dumps(authorizer_info.mini_program_info),
                func_info=json.dumps(authorization_info.func_info)
            )
            db.session.add(wx_mini_app)

            # 同步增加一个关联店铺
            new_store = Store(
                master_uid=Master.master_uid(),
                operator_id=Master.master_uid(),
                name=authorizer_info.nick_name,
                serial_no=new_serial_no,
                description=authorizer_info.signature,
                platform=1,
                type=3,
                status=1
            )
            db.session.add(new_store)

            db.session.commit()
        except Exception as err:
            db.session.rollback()
            current_app.logger.warn('Create wxapp error: %s' % str(err))
            flash('同步小程序信息失败：%s，请重试！' % str(err), 'danger')
            return render_template('wxapp/index.html', auth_status=is_auth)

        # 任务：增加小程序默认配置及API所需key
        create_wxapi_appkey.apply_async(args=[Master.master_uid(), wx_mini_app.nick_name, new_store.id])

        create_banner_spot.apply_async(args=[Master.master_uid(), 'wx_index_slide', '小程序-首页-大图轮换'])

    is_auth = True
    return render_template('wxapp/setting.html',
                           auth_status=is_auth,
                           auth_app_id=auth_app_id,
                           wx_mini_app=wx_mini_app)


@main.route('/wxapps/authorize')
def wxapp_authorize():
    """跳转授权页"""
    app_id = current_app.config['WX_APP_ID']
    back_url = '{}/open/wx/authorize_callback'.format(current_app.config['DOMAIN_URL'])
    auth_type = 2

    # 从缓存获取auth_code
    auth_code = cache.get('user_%d_wx_authorizer_auth_code' % Master.master_uid())
    if auth_code:
        return redirect('%s?auth_code=%s&is_cached=%d' % (back_url, auth_code, 1))

    # 获取预授权码
    pre_auth_code = _get_pre_auth_code()

    authorize_url = ('https://mp.weixin.qq.com/cgi-bin/componentloginpage?component_appid={}&pre_auth_code={}&'
                     'redirect_uri={}&auth_type={}').format(app_id, pre_auth_code, back_url, auth_type)

    return redirect(authorize_url)


@main.route('/wxapps/templates')
def wxapp_templates():
    """小程序模板"""
    page = request.values.get('page', 1, type=int)
    per_page = request.values.get('per_page', 10, type=int)
    auth_app_id = request.values.get('auth_app_id')

    builder = WxTemplate.query.filter_by(status=2)

    paginated_templates = builder.order_by(WxTemplate.created_at.desc()).paginate(page, per_page)

    return render_template('wxapp/wxtemplates.html',
                           auth_app_id=auth_app_id,
                           paginated_templates=paginated_templates)


@main.route('/wxapps/templates/choosed', methods=['POST'])
def wxapp_template_choosed():
    """选定模板"""
    auth_app_id = request.form.get('auth_app_id')
    template_id = request.form.get('template_id')

    current_app.logger.debug('auth id[%s], template id[%s]' % (auth_app_id, template_id))
    if not auth_app_id or not template_id:
        abort(400)

    mini_app = WxMiniApp.query.filter_by(auth_app_id=auth_app_id).first_or_404()

    # 更新模板
    mini_app.template_id = template_id

    db.session.commit()

    return status_response()


@main.route('/wxapps/service')
def wxapp_service():
    """小程序客服消息"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    auth_app_id = request.args.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取客服消息
    builder = WxServiceMessage.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id)

    builder = builder.filter_by(type=1)

    paginated_messages = builder.order_by(WxServiceMessage.create_time.desc()).paginate(page, per_page)

    return render_template('wxapp/service.html',
                           paginated_messages=paginated_messages,
                           auth_app_id=auth_app_id)


@main.route('/wxapps/service/setting', methods=['GET', 'POST'])
def wxapp_service_setting():
    """小程序客服消息推送设置"""
    if request.method == 'POST':
        auth_app_id = request.form.get('auth_app_id')
        token = request.form.get('token')
        aes_key = request.form.get('aes_key')

        if not auth_app_id or not token or not aes_key:
            abort(400)

        mini_app = WxMiniApp.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

        # 设置推送设置
        mini_app.service_token = token
        mini_app.service_aes_key = aes_key

        db.session.commit()

        flash('设置成功！', 'success')

        return redirect('%s?auth_app_id=%s' % (url_for('.wxapp_service_setting'), auth_app_id))

    # GET
    auth_app_id = request.args.get('auth_app_id')
    mini_app = WxMiniApp.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    service_token = mini_app.service_token if mini_app.service_token else gen_3rd_session_key()
    service_aes_key = mini_app.service_aes_key if mini_app.service_aes_key else make_unique_key(43)

    return render_template('wxapp/service_setting.html',
                           service_url='https://fx.taihuonio.com/open/wx/service_message',
                           service_token=service_token,
                           service_aes_key=service_aes_key,
                           auth_app_id=auth_app_id)


@main.route('/wxapps/service/reply', methods=['GET', 'POST'])
def wxapp_service_reply():
    """回复客服消息"""
    rid = request.values.get('rid')
    auth_app_id = request.values.get('auth_app_id')
    if not auth_app_id or not rid:
        abort(400)
    # 获取回复对象
    wx_service_message = WxServiceMessage.query.get(int(rid))
    form = WxReplyForm()
    if request.method == 'POST' and form.validate_on_submit():
        auth_app_id = form.auth_app_id.data
        content = form.content.data
        msg_type = form.msg_type.data

        wx_reply_message = WxServiceMessage(
            master_uid=Master.master_uid(),
            auth_app_id=auth_app_id,
            to_user=wx_service_message.from_user,
            from_user=wx_service_message.to_user,
            msg_id=wx_service_message.msg_id,
            msg_type=msg_type,
            content=content,
            type=2,
            status=2
        )
        db.session.add(wx_reply_message)
        db.session.commit()

        # 异步任务，后台发送
        reply_wxa_service.apply_async(args=[wx_reply_message.id])

        return status_response()

    return render_template('wxapp/_reply_modal.html',
                           form=form,
                           auth_app_id=auth_app_id,
                           service_message=wx_service_message)


@main.route('/wxapps/versions', methods=['GET', 'POST'])
def wxapp_versions():
    """小程序版本管理"""
    auth_app_id = request.values.get('auth_app_id')

    versions = WxVersion.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id)\
        .order_by(WxVersion.created_at.desc()).all()

    return render_template('wxapp/version_list.html',
                           versions=versions,
                           auth_app_id=auth_app_id)


@main.route('/wxapps/qrcode')
def wxapp_qrcode():
    """获取体验二维码"""
    auth_app_id = request.values.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.get_qrcode()
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': str(err)
        })

    return 'ok'


@main.route('/wxapps/get_category', methods=['GET', 'POST'])
def wxapp_category():
    """小程序可选类目"""
    auth_app_id = request.values.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取小程序信息
    mini_app = WxMiniApp.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    if request.method == 'POST':
        return status_response()

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=mini_app.master_uid, auth_app_id=auth_app_id).first_or_404()

    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.get_category()
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        abort(500)

    return render_template('wxapp/_category_modal.html',
                           category_list=result.category_list,
                           auth_app_id=auth_app_id)


@main.route('/wxapps/get_pages', methods=['GET', 'POST'])
def wxapp_pages():
    """小程序提交代码的页面配置"""
    auth_app_id = request.values.get('auth_app_id')

    if not auth_app_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.get_pages()
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': str(err)
        })

    return render_template('wxapp/_page_modal.html',
                           page_list=result.page_list,
                           auth_app_id=auth_app_id)


@main.route('/wxapps/commit', methods=['POST'])
def wxapp_commit():
    """上传小程序代码"""
    auth_app_id = request.values.get('auth_app_id')

    if not auth_app_id:
        abort(400)

    # 待提交获取小程序信息
    mini_app = WxMiniApp.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=mini_app.master_uid, auth_app_id=auth_app_id).first_or_404()

    # 获取匹配的店铺
    store = Store.query.filter_by(serial_no=mini_app.serial_no).first_or_404()

    # 获取匹配的app_key / app_secret
    client = Client.query.filter_by(store_id=store.id).first_or_404()

    ext_json = {
        "extAppid": auth_app_id,
        "ext": {
            "name": mini_app.nick_name,
            "authAppid": auth_app_id,
            "storeId": store.id,
            "attr": {
                "users": [
                    "purpen"
                ]
            },
            "api": {
                "host": "https://wx.taihuoniao.com/api",
                "version": "v1.0",
                "appKey": client.app_key,
                "appSecret": client.app_secret
            }
        }
    }
    user_version = 'v1.0'
    user_desc = mini_app.nick_name

    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.commit(mini_app.template_id, ext_json, user_version, user_desc)
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': err
        })

    try:
        # 保存版本
        new_version = WxVersion(
            master_uid=Master.master_uid(),
            auth_app_id=auth_app_id,
            template_id=mini_app.template_id,
            user_version=user_version,
            user_desc=user_desc,
            audit_at=int(timestamp())
        )
        db.session.add(new_version)
        db.session.commit()
    except Exception as err:
        current_app.logger.warn('Wxapp commit error: %s' % str(err))
        db.session.rollback()
        return custom_response(False, '上传代码失败，请稍后重试！', 400)
    
    return status_response()


@main.route('/wxapps/submit_audit', methods=['POST'])
def wxapp_submit_audit():
    """小程序提交审核"""
    auth_app_id = request.values.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)

        pages = open3rd.get_pages()

        current_app.logger.warn('pages: %s' % pages)

        categories = open3rd.get_category()

        current_app.logger.warn('categories: %s' % categories)

        tags = '创意 原创设计 智能'

        # todo: 提交审核项的一个列表（至少填写1项，至多填写5项）
        if categories:
            item = categories.category_list[0]
            item['address'] = pages.page_list[0]
            item['tag'] = tags
            item['title'] = '精选'

            item_list = [item]

            current_app.logger.warn('item_list: %s' % item_list)

            result = open3rd.submit_audit(item_list)
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': str(err)
        })

    if result:
        # 更新
        wx_version = WxVersion.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()
        wx_version.audit_id = result.auditid
        wx_version.audit_at = int(timestamp())

        db.session.commit()

    return full_response(True, R200_OK, {
        'auditid': result.auditid
    })


@main.route('/wxapps/audit_status', methods=['POST'])
def wxapp_audit_status():
    """查询某个指定版本的审核状态"""
    auth_app_id = request.values.get('auth_app_id')
    audit_id = request.values.get('audit_id')
    if not auth_app_id or not audit_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()
    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.get_audit_status(audit_id)
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': str(err)
        })

    current_app.logger.warn('wxapp audit status: %s' % result)

    # 更新状态
    wx_version = WxVersion.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()

    if result.status == 1:  # 审核失败
        wx_version.mark_audit_fail(result.reason, int(timestamp()))
    elif result.status == 0:  # 审核成功
        wx_version.mark_audit_success(int(timestamp()))
    else:  # 审核中
        wx_version.status = result.status

    db.session.commit()

    return full_response(True, R200_OK, {
        'status': result.status
    })


@main.route('/wxapps/release', methods=['POST'])
def wxapp_release():
    """发布已通过审核的小程序"""
    auth_app_id = request.form.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()
    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.release()
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': str(err)
        })
    return status_response()


@main.route('/wxapps/revert_release', methods=['POST'])
def wxapp_revert_release():
    """版本回退"""
    auth_app_id = request.form.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()
    try:
        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.revert_code_release()
    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': err
        })
    return status_response()


@main.route('/wxapps/change_status', methods=['POST'])
def wxapp_change_visit_status():
    """修改小程序线上代码的可见状态"""
    pass


@main.route('/wxapps/modify_domain', methods=['POST'])
def wxapp_modify_domain():
    """修改小程序服务器域名"""
    auth_app_id = request.form.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    # 获取授权信息
    authorizer = WxAuthorizer.query.filter_by(master_uid=Master.master_uid(), auth_app_id=auth_app_id).first_or_404()
    try:

        # 设置小程序服务器域名
        action = 'add'
        request_domain = ["https://wx.taihuoniao.com"]
        wsrequest_domain = ["wss://wx.taihuoniao.com"]
        upload_domain = ["https://wx.taihuoniao.com"]
        download_domain = ["https://wx.taihuoniao.com"]

        open3rd = WxaOpen3rd(access_token=authorizer.access_token)
        result = open3rd.modify_domain(action, request_domain, wsrequest_domain, upload_domain, download_domain)

        # 设置小程序业务域名
        webviewdomain = ["https://fx.taihuoniao.com"]
        result = open3rd.set_webview_domain(action, webviewdomain)

    except WxAppError as err:
        current_app.logger.warn('Wxapp commit is error: %s' % err)
        return status_response(False, {
            'code': 500,
            'message': err
        })
    return status_response()


@main.route('/wxapps/tester', methods=['GET', 'POST'])
def wxapp_add_tester():
    """添加体验者"""
    if request.method == 'POST':
        auth_app_id = request.form.get('auth_app_id')
        wx_account = request.form.get('wx_account')
        if not auth_app_id or not wx_account:
            abort(400)

        mini_app = WxMiniApp.query.filter_by(auth_app_id=auth_app_id).first_or_404()

        # 添加体验者
        testers = mini_app.testers
        if testers:
            testers += ',%s' % wx_account
        else:
            testers = wx_account

        mini_app.testers = testers

        db.session.commit()

        # 同步到小程序后台
        bind_wxa_tester.apply_async(args=[mini_app.master_uid, auth_app_id, wx_account])

        return render_template('wxapp/tester_list.html',
                               wx_mini_app=mini_app.to_json())

    auth_app_id = request.args.get('auth_app_id')
    if not auth_app_id:
        abort(400)

    return render_template('wxapp/_tester_modal.html',
                           auth_app_id=auth_app_id)


@main.route('/wxapps/tester/unbind', methods=['POST'])
def wxapp_unbind_tester():
    """解绑体验者"""
    auth_app_id = request.form.get('auth_app_id')
    wx_account = request.form.get('wx_account')
    if not auth_app_id or not wx_account:
        abort(400)

    mini_app = WxMiniApp.query.filter_by(auth_app_id=auth_app_id).first_or_404()

    # 删除体验者
    test_list = mini_app.test_list
    if wx_account in test_list:
        test_list.remove(wx_account)
        mini_app.testers = ','.join(test_list)

        db.session.commit()

        # 同步到小程序后台
        unbind_wxa_tester.apply_async(args=[mini_app.master_uid, auth_app_id, wx_account])

    return status_response()


def _get_authorizer_info(auth_app_id):
    """获取授权小程序账号信息"""
    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()
    # 发起请求
    wx_app_api = WxApp(component_app_id=component_app_id,
                       component_app_secret=current_app.config['WX_APP_SECRET'],
                       component_access_token=wx_token.access_token)
    result = wx_app_api.get_authorizer_info(auth_app_id)

    return result


@cache.cached(timeout=600, key_prefix='wx_pre_auth_code')
def _get_pre_auth_code():
    """获取预授权码"""
    current_app.logger.warn('get by caching...')

    component_app_id = current_app.config['WX_APP_ID']
    wx_token = WxToken.query.filter_by(app_id=component_app_id).order_by(WxToken.created_at.desc()).first()

    try:
        # 发起请求
        wx_app_api = WxApp(component_app_id=current_app.config['WX_APP_ID'],
                           component_app_secret=current_app.config['WX_APP_SECRET'],
                           component_access_token=wx_token.access_token)

        result = wx_app_api.get_pre_auth_code()
    except WxAppError as err:
        current_app.logger.warn('Request pre_auth_code error: {}'.format(err))
        return None

    return result.pre_auth_code
