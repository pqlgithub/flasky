# -*- coding: utf-8 -*-
from flask import request, abort, g, current_app, url_for
from sqlalchemy.exc import IntegrityError

from .. import db
from . import api
from .auth import auth
from .utils import *
from app.models import Asset, Directory
from app.helpers import QiniuStorage


@api.route('/assets/up_token')
def get_upload_token():
    """获取上传Token, 七牛直传模式"""
    # 生成上传token
    cfg = current_app.config
    up_token = QiniuStorage.up_token(cfg['QINIU_ACCESS_KEY'], cfg['QINIU_ACCESS_SECRET'], cfg['QINIU_BUCKET_NAME'],
                                     cfg['DOMAIN_URL'])
    up_endpoint = cfg['QINIU_UPLOAD']

    return full_response(R200_OK, {
        'up_token': up_token,
        'up_endpoint': up_endpoint
    })


@api.route('/assets')
def get_assets():
    """获取附件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    current_directory = request.args.get('directory', '')
    parent_directory = ''
    prev_url = None
    next_url = None

    # Top Level
    if current_directory == '' or current_directory is None:
        all_directory = Directory.query.filter_by(master_uid=g.master_uid, top=0).all()
        paginated_assets = Asset.query.filter_by(master_uid=g.master_uid, directory_id=0).paginate(page, per_page)
    else:
        directories = current_directory.split('/')
        # Pop last item
        last_directory_name = directories.pop()
        last_directory = Directory.query.filter_by(master_uid=g.master_uid, name=last_directory_name).first()
        if last_directory is None:
            return custom_response('此文件目录不存在！', 404, False)

        all_directory = Directory.query.filter_by(master_uid=g.master_uid, parent_id=last_directory.id).all()
        paginated_assets = last_directory.assets.paginate(page, per_page)

        # 验证是否存在父级
        if last_directory.parent_id:
            # directories.pop()
            parent_directory = '/'.join(directories)

    assets = paginated_assets.items
    if paginated_assets.has_prev:
        prev_url = url_for('api.get_assets', page=page - 1, _external=True)
    if paginated_assets.has_next:
        next_url = url_for('api.get_assets', page=page + 1, _external=True)

    return full_response(R200_OK, {
        'assets': [asset.to_json() for asset in assets],
        'prev': prev_url,
        'next': next_url,
        'count': paginated_assets.total,
        'parent_directory': parent_directory,
        'all_directory': [directory.to_json() for directory in all_directory],
    })


@api.route('/assets/<int:rid>', methods=['DELETE'])
def delete_asset(rid):
    """删除某附件"""
    pass
