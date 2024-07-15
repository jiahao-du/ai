import copy
import datetime
import re

import requests
from bs4 import BeautifulSoup


def get_wenxinyiyan():
    url = 'https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7'

    # 发送 HTTP GET 请求
    response = requests.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')

    models_pricing = {}

    rows = soup.find_all('tr')
    list_ = []
    dict_ = {
        'model_name': '',
        'manufacturer': 'Baidu',
        'input': '',
        'output': '',
        'train': '',
        'date': datetime.date.today().strftime('%Y-%m-%d'),
        'unit': 'CNY'
    }
    for row in rows:
        columns = row.find_all('td')
        dict_ = copy.deepcopy(dict_)
        if len(columns) == 4:
            if re.search(r'元/千tokens', columns[3].text.strip()) and columns[2].text.strip() == '输入':
                dict_['model_name'] = columns[0].text.strip()
                dict_['input'] = columns[3].text.strip().replace('元/千tokens', '')
            elif re.search(r'元/千tokens', columns[3].text.strip()) and columns[2].text.strip() == '-':
                dict_['model_name'] = columns[0].text.strip()
                dict_['input'] = columns[3].text.strip().replace('元/千tokens', '')
                dict_['output'] = columns[3].text.strip().replace('元/千tokens', '')
                list_.append(dict_)
            elif columns[3].text.strip() == '免费' and columns[2].text.strip() == '输入':
                dict_['model_name'] = columns[0].text.strip()
                dict_['input'] = 0
            if len(columns[0].text.strip()) > 20:
                if res := re.search(r'[A-Za-z0-9- .]+系列', dict_['model_name']):
                    dict_['model_name'] = res.group()
                    dict_['model_name'] = dict_['model_name'].replace('系列', '')
        if len(columns) == 2:
            dict_['model_name'] = dict_['model_name'].replace('系列', '')
            if columns[0].text.strip() == '输出' and re.search(r'元/千tokens', columns[1].text.strip()):
                dict_['output'] = columns[1].text.strip().replace('元/千tokens', '')
                list_.append(dict_)
            elif columns[0].text.strip() == '输出' and columns[1].text.strip() == '免费':
                dict_['output'] = 0
                list_.append(dict_)
    return list_
