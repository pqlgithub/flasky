# -*- coding: utf-8 -*-
from datetime import datetime

def timestamp2string(text, format='%Y-%m-%d %H:%M:%S'):
    """Convert int to string."""

    return datetime.fromtimestamp(text).strftime(format)