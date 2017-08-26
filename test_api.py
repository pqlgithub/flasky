# -*- coding: utf-8 -*-
import json
import urllib.request

host = 'http://jisuhuilv.market.alicloudapi.com'
path = '/exchange/single'
method = 'GET'
appcode = '16122e1e525b4cdb869d538b143fe231'
querys = 'currency=USD'
bodys = {}
url = host + path + '?' + querys

req = urllib.request.Request(url)
req.add_header('Authorization', 'APPCODE ' + appcode)
response = urllib.request.urlopen(req)
content = response.read()
if type(content) == bytes:
    content_dict = json.loads(content.decode('utf8'))
    print(content_dict['result'])