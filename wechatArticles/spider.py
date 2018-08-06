from urllib.parse import urlencode

import requests

base_url = 'http://weixin.sogou.com/weixin?'

headers = {
    'Upgrade-Insecure-Requests': 1,
    'Host': 'weixin.sogou.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
    'Cookie':'SUV=00A2178F715B283F5964530274CEC987; SUID=85E076713665860A59632AC800073520; IPLOC=CN4403; ABTEST=0|1533524129|v1; SNUID=B0DE4743323641895B310E80337126D0; weixinIndexVisited=1; sct=1; JSESSIONID=aaaCoo8CbQdZh8xo306tw'
}


def get_html(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            pass
    except ConnectionError:
        return get_html(url)


def get_index(keyword, page):
    data = {
        'query': keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
