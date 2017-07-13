# -*- coding: utf-8 -*-
import boto3
import os
import sys
import uuid
from PIL import Image
import PIL.Image

s3_client = boto3.client('s3')

def crop_image(image_path, croped_path):
    with Image.open(image_path) as image:
        # 裁切后的尺寸，正方形
        max_border = 480

        # 居中裁剪
        w, h = image.size
        if w > h:
            border = h
            crop_region = ((w - border) / 2, 0, (w + border) / 2, border)
        else:
            border = w
            crop_region = (0, (h - border) / 2, border, (h + border) / 2)

        image = image.crop(crop_region)

        # 缩放
        if border > max_border:
            image = image.resize((max_border, max_border), Image.ANTIALIAS)

        image.save(croped_path)


def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), key)
        upload_path = '/tmp/im-{}'.format(key)

        s3_client.download_file(bucket, key, download_path)
        crop_image(download_path, upload_path)
        s3_client.upload_file(upload_path, 'im{}'.format(bucket), key)