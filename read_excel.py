# -*- coding: utf-8 -*-
import sys, os
import xlrd

basedir = os.path.abspath(os.path.dirname(__file__))

file_path = '%s/app/static/tpl/mic_purchase.xlsx' % basedir

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
                        new_product['first_id_code'] = current_sheet.row(rlow)[3].value.encode('utf-8')

                if current_sheet.cell(row_idx, col_idx).ctype == 1:
                    cell_value = cell_value.encode('utf-8')

                new_product[fields[col_idx]] = cell_value

            # 转换二进制数据为字符串
            for k, v in new_product.items():
                if type(v) == bytes:
                    new_product[k] = v.decode()

            print(new_product)

            products.append(new_product)

        return products


