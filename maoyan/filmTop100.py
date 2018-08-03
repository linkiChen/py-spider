import json
import re
from multiprocessing.pool import Pool

import pymongo
import requests
import time
from requests import RequestException
from config import *


def get_page_index(url):
    print('url', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


def parse_page_index(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name"><a'
                         + '.*?/films/(\d+).*?">(.*?)</a>.*?star">(.*?)</p>.*?releasetime">(.*?)</p>'
                         + '.*?integer">(.*?)</i>.*?fraction">.*?(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'rank': item[0],
            'image': item[1],
            'index': item[2],
            'fetch_date': time.strftime('%Y-%m-%d'),
            'title': item[3],
            'actors': item[4].strip()[3:],
            'time': item[5].strip()[5:],
            'score': item[6] + item[7]

        }


def write_to_file(content):
    with open('films.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close()



client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_MAOYAN_DB]


def savet_to_mongoDb(content):
    if db[MONGO_MAOYAN_TB_TOP100].insert(content):
        print('数据成功保存到mongo', content)
        return True
    return False


def main(offset=0):
    print(offset)
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_page_index(url)
    films = parse_page_index(html)
    for film in films:
        # write_to_file(film)
        savet_to_mongoDb(film)


if __name__ == '__main__':
    # for idx in range(10):
    #     main(idx * 10)
    # main()
    pool = Pool()
    pool.map(main, [i * 10 for i in range(10)])
