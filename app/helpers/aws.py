# -*- coding: utf-8 -*-
import boto3, botocore
from flask import current_app

__all__ = [
    'connect_s3',
    'upload_file_to_s3'
]

def connect_s3():
    """Connect to AWS"""

    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY'],
        aws_secret_access_key=current_app.config['AWS_ACCESS_SECRET']
    )
    return s3


def upload_file_to_s3(s3, file, bucket_name, acl='public-read'):
    """Upload file to AWS s3"""

    try:

        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                'ACL': acl,
                'ContentType': file.content_type
            }
        )

    except Exception as e:
        print('Something Happened: ', e)
        return e

    proto = 'http://'
    if current_app.config['FLASKS3_USE_HTTPS']:
        proto = 'https://'

    return '{}{}/{}'.format(proto, current_app.config['FLASKS3_CDN_DOMAIN'], file.filename)