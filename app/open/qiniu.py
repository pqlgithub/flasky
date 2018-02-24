# -*- coding: utf-8 -*-
from flask import current_app, request

from . import open
from .. import db
from app.models import Asset, Directory
from app.utils import status_response, R400_BADREQUEST


@open.route('/qiniu/notify', methods=['POST'])
def upload_notify():
    """云存储上传回调"""
    current_app.logger.warn(request.values)

    filepath = request.values.get('filepath')
    filename = request.values.get('filename')
    filesize = request.values.get('filesize')
    mime_type = request.values.get('mime')
    width = request.values.get('width')
    height = request.values.get('height')
    master_uid = request.values.get('user_id')

    if not filepath or not master_uid or not filename:
        current_app.logger.warn('Qiniu callback params is empty!')
        return status_response(False, R400_BADREQUEST)

    # 所属的目录
    directory_id = 0
    directory = _pop_last_directory(request.values.get('directory'))
    if directory:
        current_directory = Directory.query.filter_by(master_uid=master_uid, name=directory).first()
        directory_id = current_directory.id

    # 更新记录
    new_asset = Asset(
        directory_id=directory_id,
        master_uid=master_uid,
        filepath=filepath,
        filename=filename,
        size=filesize,
        width=width,
        height=height,
        mime=mime_type
    )
    db.session.add(new_asset)
    db.session.commit()

    return status_response()


def _pop_last_directory(directory_path=None):
    """get the last directory"""
    last_directory = None
    if directory_path:
        directories = directory_path.split('/')
        # pop last item
        last_directory = directories.pop()

    return last_directory
