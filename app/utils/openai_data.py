import datetime
import re

from bs4 import BeautifulSoup


def get_openai():
    # 示例HTML数据（实际使用时，你需要从请求中获取真实的HTML页面）
    with open('openai.html', 'r', encoding='utf-8') as f:
        content = f.read()
    # 使用BeautifulSoup解析HTML数据
    soup = BeautifulSoup(content, 'html.parser')

    # 找到所有包含Model、Input、Output的容器
    models_divs = soup.find_all('div', class_='grid col-span-full grid-cols-autofit')

    # 提取出Model、Input、Output信息
    data = []
    for model_div in models_divs:
        spans = model_div.find_all('span')

        if len(spans) >= 4:
            if len(spans) >= 6:
                model = spans[0].text
                input_price = spans[1].text
                output_price = spans[5].text
            else:
                model = spans[0].text
                input_price = spans[1].text
                output_price = spans[3].text

            data.append({
                'Manufacturer': 'OpenAI',
                'Model': model,
                'Input': input_price,
                'Output': output_price,
                'Train': '',
                'Unit': 'USD',
                "Date": datetime.date.today().strftime("%Y-%m-%d"),
            })

    # 逆向遍历以避免跳过元素
    for index in range(len(data) - 1, 0, -1):
        item = data[index]
        if item['Output'] == 'training tokens':
            if 'Model' in item and item['Model']:  # 确保 Model 存在且不为空
                data[index - 2]['Train'] = item['Model']

        if item['Input'] == ' / ':
            if 'Model' in item and item['Model']:  # 确保 Model 存在且不为空
                data[index - 1]['Output'] = item['Model']
            data.pop(index)

        # print(f"Model: {item['Model']}, Input: {item['Input']}, Output: {item.get('Output', '')}")

    # 逆向遍历以避免跳过元素
    for id in range(len(data) - 1, -1, -1):
        it = data[id]
        it['Input'] = re.sub(r'\$', '', it['Input'])
        it['Output'] = re.sub(r'\$', '', it['Output'])
        it['Train'] = re.sub(r'\$', '', it['Train'])
        if (re.search(r'[a-zA-Z]+', it['Input']) or re.search(r'[a-zA-Z]+', it['Output'])
            or re.search(r'[a-zA-Z]+', it['Train'])) or float(it['Input']) > float(it['Output']):
            data.pop(id)
        else:
            if it['Input']:
                it['Input'] = float(it['Input']) / 1000
            if it['Output']:
                it['Output'] = float(it['Output']) / 1000
            if it['Train']:
                it['Train'] = float(it['Train']) / 1000
    return data