import json
import re

import os
from json import JSONDecodeError

import pymongo
import requests
from urllib.parse import urlencode
from hashlib import md5

from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from multiprocessing import Pool
from config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_TOUTIAO_DB]


def get_page_index(offset=0, keyword='美女'):
    print('offset', offset)
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': '1',
        'from': 'search_tab'
    }

    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException as e:
        print('请求索引出错', url)
        return None


def parse_page_index(html):
    try:
        keys = json.loads(str(html))
        print('has_more', keys.get('has_more'))
        if keys and 'data' in keys.keys():  # 获取json对象keys中的所有key，keys 以及key data是否存在keys中
            for item in keys.get('data'):
                if item.get('article_url'):
                    yield item.get('article_url')
    except JSONDecodeError:
        pass


# 获取团集的详情页信息

def get_page_detail(url):
    print('url', url)
    try:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
            # 'Cookie': 'tt_webid = 6584203522963047943;tt_webid = 6584203522963047943;WEATHER_CITY = % E5 % 8C % 97 % E4 % BA % AC;UM_distinctid = 164ee2df4b088b - 0f37a0d3257982 - 5e183017 - 1fa400 - 164ee2df4b1bf2;__tasessionId = 4x73i8nam1533015584597;CNZZDATA1259612802 = 2136447189 - 1533001049 - % 7C1533017249;csrftoken = dc9b3d038ea8c502fe95100ce3baa717;tt_webid = 6584203522963047943'
        }
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页出错', url)
        return None


def parse_page_detail(html, url):
    id = url[url.find('/group/', 1) + 7:len(url) - 1]

    soup = BeautifulSoup(html, 'lxml')  # 使用lxml解析html
    # title = soup.select('title')[1].get_text
    title_pattern = re.compile('title: \'.*?\',', re.S)
    title_result = re.search(title_pattern, html)
    if title_result:
        title = title_result.group(0)

    img_pattern = re.compile('gallery: JSON.parse\((.*?)\)', re.S)
    result = re.search(img_pattern, html)
    if result:
        data = json.loads(result.group(1))
        data = json.loads(data)
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            return {
                'id': id,
                'title': title,
                'url': url,
                'images': images
            }


def save_to_mongo(result):
    if db[MONGO_TOUTIAO_TB_JIEPAI].insert(result):
        print('存储到MongoDB成功', result)
        return True
    return False


def download_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return None
        return None
    except RequestException:
        print('请求图片出错', url)
        return None


def save_image(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def main():
    # html = get_page_index(1, '街拍')
    # for url in parse_page_index(html):
    #     result = get_page_detail(url)
    #     if result:
    #         imgRes = parse_page_detail(result, url)
    #         if imgRes:
    #             print('imgs')
    #         save_to_mongo(imgRes)

    offset = 0
    html = get_page_index(offset, '街拍')
    con = True
    while con:
        json_keys = json.loads(str(html))
        if json_keys and 'has_more' in json_keys.keys():
            if json_keys.get('has_more'):
                html = get_page_index(offset, '街拍')
                for url in parse_page_index(html):
                    result = get_page_detail(url)
                    if result:
                        imgRes = parse_page_detail(result, url)
                        if imgRes:
                            save_to_mongo(imgRes)
                offset += 20
        else:
            con = False


GROUP_START = 0
GROUP_END = 20


def main2(offset):
    html = get_page_index(offset, '街拍')
    for url in parse_page_index(html):
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html, url)
            save_to_mongo(result)


if __name__ == '__main__':
    # main()
    groups = [x * 20 for x in range(GROUP_START, GROUP_END + 1)]
    pool = Pool()
    pool.map(main2, groups)
