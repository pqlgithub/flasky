# -*- coding: utf-8 -*-
import enum
import time
import xlrd
import random
import hashlib
import speaklater

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from string import digits, ascii_letters
from flask import jsonify, current_app, request, flash
from flask_login import current_user
from flask._compat import text_type
from flask.json import JSONEncoder as BaseEncoder
from speaklater import _LazyString




R200_OK = { 'code': 200, 'message': 'Ok all right.' }
R201_CREATED = { 'code': 201, 'message': 'All created.' }
R204_NOCONTENT = { 'code': 204, 'message': 'All deleted.' }
R400_BADREQUEST = { 'code': 400, 'message': 'Bad request.' }
R403_FORBIDDEN = { 'code': 403, 'message': 'You can not do this.' }
R404_NOTFOUND = { 'code': 404, 'message': 'No result matched.' }
R500_BADREQUEST = { 'code': 500, 'message': 'Request failed.' }


class JSONEncoder(BaseEncoder):
    def default(self, o):
        if isinstance(o, _LazyString):
            return text_type(o)

        return BaseEncoder.default(self, o)


class Master:
    """支持多账户管理，根据当前登录用户返回主账号"""

    @staticmethod
    def master_uid():
        """获取管理员ID"""
        if current_user.is_master:
            return current_user.id
        else:
            return current_user.master_uid if current_user else None
        
    @staticmethod
    def is_can(uid):
        return uid == Master.master_uid()
        

class DBEnum(enum.Enum):

    @classmethod
    def get_enum_labels(cls):
        return [i.value for i in cls]


def create_db_session(app):
    """Connects to the database and return a session"""

    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    psql_url = app.config['SQLALCHEMY_DATABASE_URI']
    some_engine = create_engine(psql_url)

    # create a configured 'Session' class
    session = scoped_session(sessionmaker(bind=some_engine))

    return session


def timestamp():
    """return the current timestamp as an integer."""
    return time.time()


def string_to_timestamp(str_value):
    """字符串日期时间转换成时间戳"""
    d = datetime.strptime(str_value, "%Y-%m-%d %H:%M:%S")
    t = d.timetuple()
    ts = int(time.mktime(t))
    ts = float(str(ts) + str("%06d" % d.microsecond)) / 1000000

    return ts


def datestr_to_timestamp(str_value):
    """字符串日期转换成时间戳"""
    dt = datetime.strptime(str_value, "%Y-%m-%d")
    return time.mktime(dt.timetuple())


def gen_serial_no(prefix='1'):
    """生成产品编号"""
    serial_no = prefix
    serial_no += time.strftime('%y%d')
    # 生成随机数5位
    rd = str(random.randint(1, 1000000))
    z = ''
    if len(rd) < 7:
        for i in range(7-len(rd)):
            z += '0'

    return ''.join([serial_no, z, rd])


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def next_is_valid(next_url):
    """验证next url是否有效"""
    return True


def correct_int(param):
    """整数型类型转换"""
    if param is None or param == '':
        param = 0
    else:
        param = int(param)

    return param


def correct_decimal(param):
    """类型转换"""
    if param is None or param == '':
        param = 0
    else:
        param = Decimal(param)

    return param


def make_unique_key(length=20):
    """
    生成唯一key
    """
    chars = ascii_letters + digits
    
    key = ''.join(random.sample(chars, length))
    
    return key


def make_salt():
    """加盐"""
    salt = ''
    for i in range(5):
        salt = salt + random.choice(ascii_letters)
    return salt


def make_pw_hash(pw, salt=None):
    """hash加密"""
    key_bytes = pw.encode('utf-8')
    if not salt is None:
        key_bytes = key_bytes + salt.encode('utf-8')
    
    return hashlib.sha1(key_bytes).hexdigest()


def full_response(success=True, status=R200_OK, data=None):
    """结果响应：带数据和状态信息"""
    return jsonify({
        'success': success,
        'status': status,
        'data': data
    })


def status_response(success=True, status=R200_OK):
    """结果响应：状态信息"""
    return jsonify({
        'success': success,
        'status': status
    })


def custom_response(success=True, message=None, code=200):
    """自定义响应结果"""
    return status_response(success, custom_status(message, code))


def custom_status(message, code=400):
    return {
        'code': code,
        'message': message
    }


def form_errors_response(errors, code=500):
    """表单验证出错返回结果"""
    return jsonify({
        'success': False,
        'status': {
            'code': code,
            'message': errors
        }
    })


def flash_errors(form):
    """表单错误转化为字符串flash"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"%s: %s" % (
                getattr(form, field).label.text,
                error
            ))


def form_errors_list(form):
    """表单错误转化为字符串"""
    err_list = []
    for field, errors in form.errors.items():
        for error in errors:
            err_list.append({
                'field': getattr(form, field).label.text,
                'message': error
            })
    current_app.logger.warn(err_list)
    return err_list


def get_merged_cells(sheet):
    """
    获取所有的合并单元格，格式如下：
    [(4, 5, 2, 4), (5, 6, 2, 4), (1, 4, 3, 4)]
    (4, 5, 2, 4) 的含义为：行 从下标4开始，到下标5（不包含）  列 从下标2开始，到下标4（不包含），为合并单元格
    :param sheet:
    :return:
    """
    return sheet.merged_cells


def get_merged_cells_value(sheet, row_index, col_index):
    """
    先判断给定的单元格，是否属于合并单元格；
    如果是合并单元格，就返回合并单元格的内容
    :return:
    """
    merged = get_merged_cells(sheet)
    for (rlow, rhigh, clow, chigh) in merged:
        if row_index >= rlow and row_index < rhigh:
            if col_index >= clow and col_index < chigh:
                cell_value = sheet.cell_value(rlow, clow)
                return cell_value, rlow
    return None, None


def import_product_from_excel(file_path):
    """
    从采购单中读取excel的产品
    :return:
    """

    # 打开文件
    wb = xlrd.open_workbook(file_path)
    # 获取所有sheet
    for sheet_name in wb.sheet_names():
        # 根据sheet索引或名称获取sheet内容
        # sheet = wb.sheet_by_index(0)
        current_sheet = wb.sheet_by_name(sheet_name)

        # sheet 名称、行数、列数
        # print(current_sheet.name, current_sheet.nrows, current_sheet.ncols)

        # 获取整行和整列的值
        # rows = current_sheet.row_values(3)
        # cols = current_sheet.col_values(2)

        if not current_sheet.nrows:
            print('Empty sheet, continue')
            continue

        # merged_cells返回的这四个参数的含义是：(row,row_range,col,col_range),
        # 其中[row,row_range)包括row,不包括row_range,col也是一样，
        # 即(1, 3, 4, 5)的含义是：第1到2行（不包括3）合并，(7, 8, 2, 5)的含义是：第2到4列合并。
        # merge = []
        # for (rlow, rhigh, clow, chigh) in current_sheet.merged_cells:
        #    merge.append([rlow, clow])

        #for index in merge:
        #    print('%d-%d:%s' % (index[0]+1, index[1]+1, current_sheet.cell_value(index[0], index[1])))

        # 获取单元格内容
        # sheet.cell_value(1, 0).encode('utf-8')
        # sheet.row(1)[0].value.encode('utf-8')

        # 获取单元格内容的数据类型
        # sheet.cell(1, 0).ctype
        fields = ['name', 'mode', 'color', 'id_code', 'cost_price', 'quantity']

        products = []
        for row_idx in range(14, current_sheet.nrows):
            new_product = {}
            for col_idx in range(0, 6):
                cell_value = current_sheet.cell(row_idx, col_idx).value

                if cell_value is None or cell_value == '':
                    cell_value, rlow = get_merged_cells_value(current_sheet, row_idx, col_idx)
                    if cell_value is None and rlow is None:
                        continue

                    if col_idx == 0: # 以产品名称列为主
                        new_product['first_id_code'] = str(current_sheet.row(rlow)[3].value).encode('utf-8')

                if col_idx == 3: # 69码转化为字符串
                    cell_value = str(cell_value)

                if current_sheet.cell(row_idx, col_idx).ctype == 1:
                    cell_value = cell_value.encode('utf-8')

                current_app.logger.debug('%d-%d: %s' % (row_idx+1, col_idx+1, cell_value))

                new_product[fields[col_idx]] = cell_value

            # 转换二进制数据为字符串
            for k, v in new_product.items():
                if type(v) == bytes:
                    new_product[k] = v.decode()

            products.append(new_product)

        return products


def split_huazhu_address(address_str):
    """地址字符串转换为省、市、区、地址"""
    
    addr_ary = address_str.split('-')
    province = ''
    city = ''
    area = ''
    if len(addr_ary) > 1:
        province = addr_ary.pop(0)
    if len(addr_ary) > 1:
        city = addr_ary.pop(0)
    if len(addr_ary) > 1:
        area = addr_ary.pop(0)
    
    address = '-'.join(addr_ary)
    
    return province, city, area, address


def make_cache_key(*args, **kwargs):
    """生成缓存唯一Key"""
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    # lang = get_locale()
    lang = 'zh_cn'
    return (path + args + lang).encode('utf-8')


class Map(dict):
    """
    提供字典的dot访问模式
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    if isinstance(v, dict):
                        v = Map(v)
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                if isinstance(v, dict):
                    v = Map(v)
                self[k] = v

    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getitem__(self, key):
        if key not in self.__dict__:
            super(Map, self).__setitem__(key, {})
            self.__dict__.update({key: Map()})
        return self.__dict__[key]

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]


def make_verifycode_img():
    """生产验证码图片"""
    # 生成验证码背景颜色
    def get_background_color():
        return (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))

    # 生成验证码文字颜色
    def get_font_color():
        return (random.randint(101, 255), random.randint(101, 255), random.randint(101, 255))

    # 生成验证码单个文字
    def get_random_char():
        random_num=str(random.randint(0,9))
        random_upper_alph=chr(random.randint(65,90))
        random_lowwer_alph=chr(random.randint(97,122))
        random_char=random.choice([random_num,random_lowwer_alph,random_upper_alph])

        return random_char

    image = Image.new(mode="RGB", size=(260, 40), color=get_background_color())
    draw=ImageDraw.Draw(image,mode="RGB")
    font=ImageFont.truetype('app/static/fonts/kumo.ttf',size=32)

    verifycode=""
    for i in range(1,6):
        char=get_random_char()
        verifycode+=char
        draw.text([i*40,5],char,get_font_color(),font=font)

    width=260
    height=40
    for i in range(80):
        draw.point((random.randint(0,width),random.randint(0,height)),fill=get_background_color())

    for i in range(10):
        x1=random.randint(0,width)
        x2=random.randint(0,width)
        y1=random.randint(0,height)
        y2=random.randint(0,height)
        draw.line((x1,y1,x2,y2),fill=get_background_color())
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=get_background_color())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=get_background_color())

    f=BytesIO()
    image.save(f, "png")
    data=f.getvalue()

    return verifycode,data


def make_phoneverifycode():
    """生成手机验证码"""
    phoneverifycode = ''
    for i in range(4):
        random_num = str(random.randint(0, 9))
        phoneverifycode += random_num
    return phoneverifycode