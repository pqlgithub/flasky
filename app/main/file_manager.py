# -*- coding: utf-8 -*-
import os, time, hashlib, re
from os.path import splitext,getsize
from PIL import Image
from flask import current_app, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from wtforms import ValidationError

from app import db, uploader
from app.models import Asset, Directory
from . import main

from ..decorators import user_has, user_is
from app.utils import full_response, status_response, Master
from app.helpers import aws

@main.route('/file_manager/folder', methods=['POST'])
@main.route('/file_manager/folder/<int:page>', methods=['POST'])
@login_required
def folder(page=1):
    parent_id = 0
    top = 0
    success = True

    if request.method == 'POST':
        sub_folder = request.form.get('folder')
        parent_directory = request.form.get('parent_directory', '')

        if parent_directory != '':
            directories = parent_directory.split('/')
            # pop last item
            last_directory_name = directories.pop()
            last_directory = Directory.query.filter_by(name=last_directory_name).first()

            parent_id = last_directory.id
            top = 1

        try:
            directory = Directory(name=sub_folder, master_uid=current_user.id, parent_id=parent_id, top=top)

            db.session.add(directory)
            db.session.commit()

        except ValidationError:
            success = False

    return status_response(success)


@main.route('/file_manager/show_asset')
@main.route('/file_manager/show_asset/<int:page>')
def show_asset(page=1):
    per_page = 20
    parent_directory = ''
    all_directory = None
    paginated_assets = None

    current_directory = request.args.get('directory', '')
    up_target = request.args.get('up_target', 'mic')
    # top level
    if current_directory == '' or current_directory is None:
        all_directory = Directory.query.filter_by(top=0).all()
        paginated_assets = Asset.query.filter_by(directory_id=0).paginate(page, per_page)
    else:
        directories = current_directory.split('/')
        # pop last item
        last_directory_name = directories.pop()
        last_directory = Directory.query.filter_by(name=last_directory_name).first()

        all_directory = Directory.query.filter_by(parent_id=last_directory.id).all()
        paginated_assets = last_directory.assets.paginate(page, per_page)

        # 验证是否存在父级
        if last_directory.parent_id:
            # directories.pop()
            parent_directory = '/'.join(directories)

    return render_template('file_manager.html',
                           up_target=up_target,
                           current_directory=current_directory,
                           parent_directory=parent_directory,
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
    saved_asset_ids = []
    sub_folder = str(time.strftime('%y%m%d'))
    directory_id = 0
    root_folder = 'asset'

    directory = _pop_last_directory()
    if directory:
        current_directory = Directory.query.filter_by(name=directory).first()
        directory_id = current_directory.id

    s3 = aws.connect_s3()
    # for key, file in request.files.iteritems():
    for f in request.files.getlist('file'):
        upload_name = f.filename
        mime_type = f.mimetype

        # Gen new file name
        file_ext = splitext(f.filename)[1].lower()
        name_prefix = 'mis' + str(time.time())
        name_prefix = hashlib.md5(name_prefix.encode('utf-8')).hexdigest()[:15]
        #filename = '%s/%s/%s%s' % (root_folder, sub_folder, name_prefix, file_ext)
        filename = '%s%s' % (name_prefix, file_ext)

        current_app.logger.debug('File length: %s,%s' % (f.content_length, f.mimetype))

        if not current_app.config['DEBUG']:
            # Upload to s3
            f.filename = filename
            out_result = aws.upload_file_to_s3(s3, f, current_app.config['ASSET_BUCKET_NAME'])
            # response = s3.head_object(Bucket=current_app.config['FLASKS3_BUCKET_NAME'], Key=filename)
        else:
            # Upload to local
            filename = uploader.save(f, folder=sub_folder, name=name_prefix + '.')
            # Get info of upload image
            # img = Image.open(f)
            # img.load()

        width = 0 #img.size[0]
        height = 0 #img.size[1]

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
    path_list = request.form.getlist('path[]')

    current_app.logger.debug('delete path list %s' % path_list)

    for filepath in path_list:
        if re.match(r'([a-zA-Z0-9]+\/)?[0-9]{6}\/\w{15}\.\w{3,4}$', filepath):
            asset = Asset.query.filter_by(filepath=filepath).first()
            db.session.delete(asset)
        else:
            last_directory = _pop_last_directory(filepath)
            directory = Directory.query.filter_by(name=last_directory).first()
            if directory:
                db.session.delete(directory)

        db.session.commit()

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