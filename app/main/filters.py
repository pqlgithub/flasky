# -*- coding: utf-8 -*-
from datetime import datetime
from os.path import splitext

__all__ = [
    'timestamp2string',
    'short_filename',
    'supress_none',
    'break_line'
]

def timestamp2string(text, format='%Y-%m-%d %H:%M:%S'):
    """Convert int to string."""

    return datetime.fromtimestamp(text).strftime(format)


def short_filename(text, length=10):
    """Replace a string use *."""

    if len(text) < length:
        return text
    prefix = text[:length]
    file_ext = splitext(text)[1].lower()
    return prefix + '*' + file_ext


def supress_none(val):
    """抑制输出None"""

    return val if val is not None else ''


def break_line(text, length=10):
    """强制添加换行符"""

    if len(text) <= length:
        return text

    return text[:length] + '<br>' + text[length:]

