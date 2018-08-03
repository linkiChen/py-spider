import re

import pymongo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *

PHJS_CFG = ['--disk-cache=true']

# browser = webdriver.Chrome()
browser = webdriver.PhantomJS(service_args=PHJS_CFG)
wait = WebDriverWait(browser, 15)


def search():
    try:
        browser.get('https://www.taobao.com')
        # 使用css选择器获取搜索输入框
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        # 获取搜索按钮
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))
        )
        # 输入框输入
        input.send_keys('美食')
        # 点击搜索
        submit.click()
        # 获取搜索结果总页数
        total_page = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total'))
        )
        # 第一页加载完，解析商品信息
        get_products()
        return total_page.text
    except TimeoutException:
        print('read timeout')
        return search()


def next_page(page_number):
    try:
        # 跳转页输入框
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        # 跳转页确定按钮
        submit = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit'))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()

        wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active'),
                str(page_number)))
        # 跳转页完成后,解析商品信息
        get_products()
    except TimeoutException:
        next_page(page_number)


def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    # print('html',html)
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'item_id': (item.find('.title')('.J_ClickStat')).attr('data-nid'),
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text()[2:],
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop_user_id': (item.find('.shop')('.shopname')).attr('data-userid'),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        # print(product)
        savet_to_mongoDb(product)


client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_TAOBAO_DB]


def savet_to_mongoDb(content):
    try:
        if db[MONGO_TAOBAO_TB_MEISHI].insert(content):
            print('数据成功保存到mongo', content)
    except Exception:
        print('保存数据失败:', content)


def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))
        for page_idx in range(2, total + 1):
            next_page(page_idx)
    except Exception:
        print('搜索商品出错')
    finally:
        browser.close()


if __name__ == '__main__':
    main()
