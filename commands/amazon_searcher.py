# -*- coding: utf-8 -*-
import ssl
from urllib import request, parse, error
from bs4 import BeautifulSoup
from openpyxl.reader.excel import load_workbook
from openpyxl.workbook import Workbook


def searcher():
    word = parse.quote_plus('power bank')
    url = 'https://www.amazon.com/s/ref=nb_sb_noss_2?url=search-alias%3Daps&field-keywords={}'.format(word)

    headers = {
        'User-Agent': r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36 115Browser/6.0.3',
        'Referer': r'http://www.baidu.com',
        'Connection': 'keep-alive'
    }

    try:
        ssl._create_default_https_context = ssl._create_unverified_context

        print('Start to request [%s]' % url)

        req = request.Request(url)

        response = request.urlopen(req).read()
        response = response.decode('utf-8')

        print('Request is ok.')

        soup = BeautifulSoup(response, 'html.parser')

        h2 = soup.find_all(id="s-result-count")

        count_text = h2.string

        print('Count [%s]' % count_text)

    except error.HTTPError as ex:
        print(ex.code())
        print(ex.read().decode('utf-8'))