#-*- coding:utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
from config import *
import pymongo
client = pymongo.MongoClient(MONGODB_URL)
db = client[MONGODB_DB]

chrome = webdriver.Chrome()
wait = WebDriverWait(chrome, 10)
def search(keyword):
    try:
        chrome.get("https://www.taobao.com")
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#J_TSearchForm > div.search-button > button"))
        )
        input.send_keys(keyword)
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.total"))
        )
        parse_page()
        return total.text
    except TimeoutException:
        return search(keyword)

def next_page(page):
    try:
        input =  wait.until(

                EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
            )
        submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )
        input.clear()
        input.send_keys(page)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > ul > li.item.active"),str(page))
        )
        parse_page()
    except TimeoutException:
        next_page(page)

def parse_page():
    html = chrome.page_source
    doc = pq(html)
    items = doc("#mainsrp-itemlist .items .item").items()
    for item in items:
        product = {
            'image':item.find(".pic .img").attr("data-src"),
            'price':item.find(".price").text(),
            'location':item.find(".location").text(),
            'shopname':item.find(".shopname").text(),
        }
        save_to_mongo(product)

def save_to_mongo(result):
    try:
        if db[MONGODB_TABLE].insert(result):
            print("存储到MONGODB成功", result)
    except Exception:
        print("存储到MONGDB失败",result)

def main(keyword):
    total = search(keyword)
    p = re.compile("(\d+)")
    m = p.search(total)
    if m:
        pages = int(m.group())
        for page in range(2,pages+1):
            next_page(page)

if __name__ == "__main__":
    main("美食")