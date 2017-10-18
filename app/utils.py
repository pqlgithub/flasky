# -*- coding: utf-8 -*-
import enum, time, random, xlrd
from datetime import datetime
from flask import jsonify, current_app
from flask_login import current_user

R200_OK = { 'code': 200, 'message': 'Ok all right.' }
R201_CREATED = { 'code': 201, 'message': 'All created.' }
R204_NOCONTENT = { 'code': 204, 'message': 'All deleted.' }
R400_BADREQUEST = { 'code': 400, 'message': 'Bad request.' }
R403_FORBIDDEN = { 'code': 403, 'message': 'You can not do this.' }
R404_NOTFOUND = { 'code': 404, 'message': 'No result matched.' }
R500_BADREQUEST = { 'code': 500, 'message': 'Request failed.' }



class Master:
    """支持多账户管理，根据当前登录用户返回主账号"""

    @staticmethod
    def master_uid():
        """获取管理员ID"""
        if current_user.is_master:
            return current_user.id
        else:
            return current_user.master_uid if current_user else None

class DBEnum(enum.Enum):

    @classmethod
    def get_enum_labels(cls):
        return [i.value for i in cls]

def create_db_session():
    # create a new session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    psql_url = current_app.config['SQLALCHEMY_DATABASE_URI']
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
    timestamp = int(time.mktime(t))
    timestamp = float(str(timestamp) + str("%06d" % d.microsecond)) / 1000000

    return timestamp


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
        if (row_index >= rlow and row_index < rhigh):
            if (col_index >= clow and col_index < chigh):
                cell_value = sheet.cell_value(rlow, clow)
                return (cell_value, rlow)
    return (None, None)


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
    
    province = addr_ary.pop(0)
    city = addr_ary.pop(0)
    area = addr_ary.pop(0)
    address = '-'.join(addr_ary)
    
    return (province, city, area, address)
    