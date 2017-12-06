# -*- coding: utf-8 -*-
import random, string, time

__all__ = [
    'Dictate',
    'MixGenId'
]

class Dictate(object):
    """Object view of a dict, updating the passed in dict when values are set
        or deleted. "Dictate" the contents of a dict...: """

    def __init__(self, d):
        # since __setattr__ is overridden, self.__dict = d doesn't work
        object.__setattr__(self, '_Dictate__dict', d)

    # Dictionary-like access / updates
    def __getitem__(self, name):
        value = self.__dict[name]
        if isinstance(value, dict):  # recursively view sub-dicts as objects
            value = Dictate(value)
        return value

    def __setitem__(self, name, value):
        self.__dict[name] = value
    
    def __delitem__(self, name):
        del self.__dict[name]

    # Object-like access / updates
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.__dict)

    def __str__(self):
        return str(self.__dict)
    


class MixGenId():
    """生成各种sn/sku"""
    
    @staticmethod
    def gen_digits(self, length=7):
        """生成数字串"""
        return ''.join(random.sample(string.digits, length))
    
    
    @staticmethod
    def gen_letters(self, length=20):
        """生成字符串"""
        return ''.join(random.sample(string.ascii_letters, length))
    
    
    @staticmethod
    def gen_brand_sn(length=8):
        """生成品牌sn"""
        prefix = '6'
        return ''.join([prefix, MixGenId.gen_digits(length)])
    
    
    @staticmethod
    def gen_product_sku(length=9):
        """生成商品sku"""
        prefix = '8'
        return ''.join([prefix, MixGenId.gen_digits(length)])

    
    @staticmethod
    def gen_shop_sn(length=7):
        """生成商店sn"""
        prefix = '9'
        return ''.join([prefix, MixGenId.gen_digits(length)])
    
    
    @staticmethod
    def gen_user_xid(length=10):
        prefix = '1'
        return ''.join([prefix, MixGenId.gen_digits(length)])
    