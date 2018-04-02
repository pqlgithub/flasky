# -*- coding: utf-8 -*-
import os, time, hashlib, re
from urllib import parse
from os.path import splitext,getsize
from PIL import Image
from flask import current_app, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from flask_babelex import gettext
from wtforms import ValidationError
from pymysql.err import IntegrityError

from app import db, uploader
from . import main
from app.models import Asset, Directory
from app.utils import timestamp, status_response, Master, custom_response, R400_BADREQUEST
from app.helpers import MixGenId, QiniuStorage


@main.route('/file_manager/folders')
def get_folders():
    """获取目录结构"""
    pid = request.values.get('pid', 0)
    _type = request.values.get('type', 'all')

    directories = Directory.query.filter_by(master_uid=Master.master_uid(), parent_id=pid).all()

    if _type == 'children':
        return render_template('assets/_children_folder.html',
                               pid=pid,
                               directories=directories)

    return render_template('assets/_modal_directory.html',
                           pid=pid,
                           move_folder_url=url_for('.move_folder'),
                           directories=directories)


@main.route('/file_manager/folders/move', methods=['POST'])
def move_folder():
    """移动到某个目录"""
    select_folder_id = request.form.get('select_folder_id', 0, type=int)
    folders = request.form.get('folders')
    files = request.form.get('files')
    if not select_folder_id:
        return custom_response(False, '未选择移动至目录')
    if not folders and not files:
        return status_response(False, R400_BADREQUEST)

    if folders:
        folder_ids = folders.split(',')
        for folder_id in folder_ids:
            directory = Directory.query.get(int(folder_id))
            if not directory:
                continue

            # 验证不能移动自己的子目录里
            if Directory.is_children(Master.master_uid(), directory.id, select_folder_id):
                return custom_response(False, '不能设置到自己的子目录中')

            directory.parent_id = select_folder_id

    if files:
        file_ids = files.split(',')
        for file_id in file_ids:
            asset = Asset.query.get(int(file_id))
            asset.directory_id = select_folder_id

    db.session.commit()

    return status_response(True)


@main.route('/file_manager/folders/rename', methods=['GET', 'POST'])
def rename_folder():
    """重命名某个目录"""
    folder_id = request.values.get('folder_id', 0, type=int)
    if not folder_id:
        return custom_response(False, '未选择目录')

    directory = Directory.query.get(folder_id)
    if not directory or not Master.is_can(directory.master_uid):
        return custom_response(False, '该目录您无权操作')

    if request.method == 'POST':
        new_name = request.form.get('new_name')
        # 验证目录
        if new_name is None or new_name == '':
            return custom_response(False, gettext("Directory name isn't empty!"))

        # 截取头尾空格
        new_name = new_name.strip()
        # 替换中间空格符
        new_name = re.sub(r'\s+', '_', new_name)
        pattern = re.compile(r'[!#@\$\/%\?&]')
        if len(pattern.findall(new_name)):
            return custom_response(False, gettext("Directory name can't contain special characters [!#@$/?&]!"))

        # 验证同级目录是否存在相同名称
        if Directory.query.filter_by(master_uid=Master.master_uid(), parent_id=directory.parent_id, name=new_name).first():
            return custom_response(False, gettext("Directory name is already exist!"))

        directory.name = new_name

        db.session.commit()

        return status_response()

    return render_template('assets/_modal_rename.html',
                           rename_folder_url=url_for('.rename_folder'),
                           directory=directory)


@main.route('/file_manager/folder', methods=['POST'])
def folder():
    top = 0
    success = True

    if request.method == 'POST':
        sub_folder = request.form.get('folder')
        parent_id = request.form.get('parent_id', 0)

        sub_folder = parse.unquote(sub_folder)
        # 截取头尾空格
        sub_folder = sub_folder.strip()
        # 验证目录
        if sub_folder is None or sub_folder == '':
            return custom_response(False, gettext("Directory name isn't empty!"))

        # 替换中间空格符
        sub_folder = re.sub(r'\s+', '_', sub_folder)
        pattern = re.compile(r'[!#@\$\/%\?&]')
        if len(pattern.findall(sub_folder)):
            return custom_response(False, gettext("Directory name can't contain special characters [!#@$/?&]!"))

        # 验证同级目录是否存在相同名称
        if Directory.query.filter_by(master_uid=Master.master_uid(), parent_id=parent_id, name=sub_folder).first():
            return custom_response(False, gettext("Directory name is already exist!"))

        if parent_id:
            top = 1

        try:
            directory = Directory(
                name=sub_folder,
                master_uid=Master.master_uid(),
                parent_id=parent_id,
                top=top
            )

            db.session.add(directory)

            db.session.commit()

        except ValidationError as err:
            current_app.logger.warn('Create folder error: %s' % str(err))
            success = False

    return status_response(success)


@main.route('/file_manager/show_asset')
@main.route('/file_manager/show_asset/<int:page>')
def show_asset(page=1):
    per_page = request.values.get('per_page', 25, type=int)
    parent_directory = ''
    parent_id = 0
    all_directory = []
    paginated_assets = []

    current_directory = request.args.get('directory', '')
    current_directory_id = request.args.get('directory_id', 0)
    up_target = request.args.get('up_target', 'mic')
    # top level
    if current_directory == '' or not current_directory or not current_directory_id:
        all_directory = Directory.query.filter_by(master_uid=Master.master_uid(), parent_id=0).all()
        paginated_assets = Asset.query.filter_by(master_uid=Master.master_uid(), directory_id=0).paginate(page, per_page)
        # current_directory，current_directory_id不匹配，则重置
        current_directory = ''
        current_directory_id = 0
    else:
        directories = current_directory.split('/')

        # 删除最末文件夹
        last_directory_name = directories.pop()
        current_app.logger.debug('Directory name: [%s]' % last_directory_name)

        last_directory = Directory.query.get(int(current_directory_id))

        if last_directory:
            all_directory = Directory.query.filter_by(master_uid=Master.master_uid(), parent_id=last_directory.id).all()
            paginated_assets = last_directory.assets.paginate(page, per_page)

            # 验证是否存在父级
            if last_directory.parent_id:
                # directories.pop()
                parent_directory = '/'.join(directories)
                parent_id = last_directory.parent_id

    # 生成上传token
    cfg = current_app.config
    up_token = QiniuStorage.up_token(cfg['QINIU_ACCESS_KEY'], cfg['QINIU_ACCESS_SECRET'], cfg['QINIU_BUCKET_NAME'],
                                     cfg['DOMAIN_URL'])
    if current_app.config['MODE'] == 'prod':
        up_endpoint = cfg['QINIU_UPLOAD']
    else:
        up_endpoint = url_for('main.flupload')

    return render_template('file_manager.html',
                           up_target=up_target,
                           up_endpoint=up_endpoint,
                           up_token=up_token,
                           master_uid=Master.master_uid(),
                           current_directory=current_directory,
                           current_directory_id=current_directory_id,
                           parent_directory=parent_directory,
                           parent_id=parent_id,
                           all_directory=all_directory,
                           paginated_assets=paginated_assets)


@main.route('/file_manager/get_asset/<int:id>')
def get_asset(id):
    asset = Asset.query.get_or_404(id)
    return jsonify(asset.to_json())


@main.route('/file_manager/view_asset/<int:id>')
def view_asset(id):
    asset = Asset.query.get_or_404(id)
    return jsonify(asset.to_json())


@main.route('/file_manager/flupload', methods=['POST'])
def flupload():
    """开发环境文件上传，生产环境使用七牛直传"""
    saved_asset_ids = []
    sub_folder = str(time.strftime('%y%m%d'))
    directory_id = 0
    root_folder = 'asset'

    directory = _pop_last_directory()
    if directory:
        current_directory = Directory.query.filter_by(master_uid=Master.master_uid(), name=directory).first()
        directory_id = current_directory.id
    else:
        # 获取默认目录
        current_directory = Directory.query.filter_by(master_uid=Master.master_uid(), is_default=True).first()
        directory_id = current_directory.id if current_directory else 0

    # for key, file in request.files.iteritems():
    for f in request.files.getlist('file'):
        upload_name = f.filename
        mime_type = f.mimetype

        # Gen new file name
        file_ext = splitext(f.filename)[1].lower()
        name_prefix = 'fx' + str(time.time())
        name_prefix = hashlib.md5(name_prefix.encode('utf-8')).hexdigest()[:15]
        filename = '%s/%s/%s%s' % (root_folder, sub_folder, name_prefix, file_ext)

        # Upload to local
        filename = uploader.save(f, folder=sub_folder, name=name_prefix + '.')

        current_app.logger.warn('path: %s' % uploader.path(filename))

        # Get info of upload image
        img = Image.open(uploader.path(filename))
        img.load()
        width = img.size[0]
        height = img.size[1]

        # Update to DB
        new_asset = Asset(
            master_uid=Master.master_uid(),
            filepath=filename,
            filename=upload_name,
            directory_id=directory_id,
            width=width,
            height=height,
            mime=mime_type
        )
        db.session.add(new_asset)
        db.session.commit()

        saved_asset_ids.append(new_asset.id)

    return jsonify({
        'status': 200,
        'ids': saved_asset_ids
    })


@main.route('/file_manager/pldelete', methods=['POST'])
def pldelete():
    folders = request.form.get('folders')
    files = request.form.get('files')
    if not folders and not files:
        return status_response(False, R400_BADREQUEST)

    try:
        if folders:
            folder_ids = folders.split(',')
            for folder_id in folder_ids:
                directory = Directory.query.get(int(folder_id))
                if not directory:  # 不存在则跳过
                    continue

                if not Master.is_can(directory.master_uid):
                    return custom_response(False, '您无权进行删除操作！')

                # 如有子文件夹，不能删除
                if Directory.query.filter_by(master_uid=Master.master_uid(), parent_id=directory.id).first():
                    return custom_response(False, '此文件夹下有子文件夹,不能删除！')

                # 如有子元素，不能删除
                if directory.assets.count():
                    return custom_response(False, '此文件夹正在使用中,不能删除！')

                db.session.delete(directory)

        if files:
            file_ids = files.split(',')
            for file_id in file_ids:
                asset = Asset.query.get(int(file_id))
                if not asset:  # 不存在则跳过
                    continue

                if not Master.is_can(asset.master_uid):
                    return custom_response(False, '您无权进行删除操作！')

                db.session.delete(asset)

        db.session.commit()
    except Exception as err:
        db.session.rollback()
        current_app.logger.warn('Pldelete asset error: %s' % err)
        return custom_response(False, '此图正在被使用中,不能被删！')

    return status_response()


def _pop_last_directory(directory_path=None):
    directory_path = request.form.get('directory') if directory_path is None else directory_path
    """get the last directory"""
    last_directory = None
    if directory_path:
        directories = directory_path.split('/')
        # pop last item
        last_directory = directories.pop()
    return last_directory
