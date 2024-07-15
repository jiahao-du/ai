import datetime
import re

import requests
from bs4 import BeautifulSoup


def get_tongyiqianwen():
    # URL对象，替换成你需要访问的URL
    url = 'https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-thousand-questions-metering-and-billing'

    # 发送 HTTP GET 请求
    response = requests.get(url)

    list_ = []
    # 检查响应状态, 确保请求成功
    if response.status_code == 200:
        # 解析网页内容
        soup = BeautifulSoup(response.content, 'html.parser')

        # 查找表格数据
        tables = soup.find_all("table")

        for idx, table in enumerate(tables):
            print(f"\n表格 {idx + 1}：")
            rows = table.find_all("tr")

            rowspan_tracker = {}  # 用于跟踪跨行的列
            for row_idx, row in enumerate(rows):
                cols = row.find_all(["td", "th"])

                effective_cols = []  # 当前行的实际列数据

                col_span_idx = 0
                for col in cols:
                    # 理解rowspan
                    rowspan = int(col.get("rowspan", 1))

                    # 考虑之前的rowspan
                    while col_span_idx in rowspan_tracker and rowspan_tracker[col_span_idx][1] > 0:
                        effective_cols.append(rowspan_tracker[col_span_idx][0])
                        rowspan_tracker[col_span_idx] = (
                            rowspan_tracker[col_span_idx][0], rowspan_tracker[col_span_idx][1] - 1)
                        col_span_idx += 1

                    effective_cols.append(col.get_text(strip=True))

                    if rowspan > 1:
                        rowspan_tracker[col_span_idx] = (col.get_text(strip=True), rowspan - 1)

                    col_span_idx += 1

                # 确保处理剩余跟踪中的rowspan
                while col_span_idx in rowspan_tracker and rowspan_tracker[col_span_idx][1] > 0:
                    effective_cols.append(rowspan_tracker[col_span_idx][0])
                    rowspan_tracker[col_span_idx] = (
                        rowspan_tracker[col_span_idx][0], rowspan_tracker[col_span_idx][1] - 1)
                    col_span_idx += 1

                if len(effective_cols) >= 5:
                    model_service = effective_cols[0]
                    model_spec = effective_cols[1]
                    input_price = effective_cols[2]
                    output_price = effective_cols[3]
                    billing_mode = effective_cols[4]

                    print(f"模型服务: {model_service}")
                    print(f"模型规格: {model_spec}")
                    print(f"输入价格: {input_price}")
                    print(f"输出价格: {output_price}")
                    print(f"计费模式: {billing_mode}")
                    if (model_service and model_spec and re.search(r'\d+', input_price)
                            and re.search(r'\d+', output_price) and billing_mode):
                        input_price = re.sub(r'元/1,000 tokens', '', input_price)
                        output_price = re.sub(r'元/1,000 tokens', '', output_price)
                        if re.search(r'[a-zA-Z]+', input_price) or re.search(r'[a-zA-Z]+', output_price):
                            continue
                        list_.append({
                            "manufacturer": "Aliyun",
                            "model_name": model_spec,
                            "input_price": input_price,
                            "output_price": output_price,
                            "unit": "CNY",
                            "date": datetime.date.today().strftime("%Y-%m-%d"),
                        })
                    print("=" * 20)
                else:
                    print("这行没有足够的列数，已跳过：", effective_cols)
    else:
        print(f"HTTP请求失败，状态码: {response.status_code}")
    return list_
