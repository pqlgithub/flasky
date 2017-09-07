# -*- coding: utf-8 -*-
import json
import hashlib
import base64
import urllib
import urllib.request
import urllib.parse
from flask import current_app


def encrypt(origin_data, app_key):
    """数据内容签名：把(请求内容(未编码)+AppKey)进行MD5加密，然后Base64编码"""

    m = hashlib.md5()
    m.update((origin_data + app_key).encode('utf8'))
    encode_str = m.hexdigest()
    base64_text = base64.b64encode(encode_str.encode(encoding='utf-8'))

    return base64_text


def send_post(url, data):
    """发送post请求"""

    post_data = urllib.parse.urlencode(data).encode('utf-8')
    header = {
        'Accept': 'application/x-www-form-urlencoded;charset=utf-8',
        'Accept-Encoding': 'utf-8'
    }
    req = urllib.request.Request(url, post_data, header)
    get_data = (urllib.request.urlopen(req).read().decode('utf-8'))

    return get_data


def get_company(logistic_code, app_id, app_key, url):
    """获取对应快递单号的快递公司代码和名称"""

    data = {
        'LogisticCode': logistic_code
    }
    d = json.dumps(data, sort_keys=True)
    request_data = encrypt(d, app_key)
    post_data = {
        'RequestData': d,
        'EBusinessID': app_id,
        'RequestType': '2002',
        'DataType': '2',
        'DataSign': request_data.decode()
    }
    json_data = send_post(url, post_data)
    sort_data = json.loads(json_data)

    return sort_data


def get_trace(logistic_code, shipper_code, app_id, app_key, url):
    """查询接口支持按照运单号查询(单个查询)"""

    data = {
        'LogisticCode': logistic_code,
        'ShipperCode': shipper_code
    }

    d = json.dumps(data, sort_keys=True)
    request_data = encrypt(d, app_key)
    post_data = {
        'RequestData': d,
        'EBusinessID': app_id,
        'RequestType': '1002',
        'DataType': '2',
        'DataSign': request_data.decode()
    }
    json_data = send_post(url, post_data)
    sort_data = json.loads(json_data)

    return sort_data


def get_eorder(eorder):
    """获取电子面单信息"""
    
    url = current_app.config['KDN_APP_ROOT_URL'] + '/EOrderService'
    d = json.dumps(eorder, sort_keys=True)
    request_data = encrypt(d, current_app.config['KDN_APP_KEY'])

    post_data = {
        'RequestData': d,
        'EBusinessID': current_app.config['KDN_APP_ID'],
        'RequestType': '1007',
        'DataSign': request_data.decode(),
        'DataType': 2
    }
    json_data = send_post(url, post_data)
    sort_data = json.loads(json_data)

    return sort_data


def track_express(express_code):
    """查询物流信息"""

    url = 'http://testapi.kdniao.cc:8081/Ebusiness/EbusinessOrderHandle.aspx'
    data = get_company(express_code, current_app.config['KDN_APP_ID'], current_app.config['KDN_APP_KEY'], url)
    if not any(data['Shippers']):
        current_app.logger.warn('未查到该快递信息,请检查快递单号是否有误！')
    else:
        trace_data = get_trace(express_code, data['Shippers'][0]['ShipperCode'], current_app.config['KDN_APP_ID'],
                               current_app.config['KDN_APP_KEY'], url)
        if trace_data['Success'] == 'false' or not any(trace_data['Traces']):
            current_app.logger.warn('未查询到该快递物流轨迹!')
        else:
            str_state = '问题件'
            if trace_data['State'] == '2':
                str_state = '在途中'
            if trace_data['State'] == '3':
                str_state = '已签收'

            trace_data = trace_data['Traces']
            item_no = 1
            for item in trace_data:
                current_app.logger.warn(str(item_no) + ':', item['AcceptTime'], item['AcceptStation'])
                item_no += 1

    return





