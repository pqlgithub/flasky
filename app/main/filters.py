# -*- coding: utf-8 -*-
from datetime import datetime
from os.path import splitext

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