import os
import threading
import json
import queue
from sys import platform as _platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import Proxy
import time
import ElasticSearch
import random
from multiprocessing import Process


SEARCH_URL = "https://www.amazon.com/s/ref=nb_sb_noss_2?url=search-alias%3Daps&field-keywords="
PRODUCT_URL = "https://www.amazon.com/dp/"
search_fields = [
    "iphone",
    "mobile",
    "beauty",
    "hair",
    "apple",
    "macbook",
    "calcukator",
    "pen",
    "glass",
    "note 8",
    "samsung",
    "wallet",
    "watch"
]
products = []
processes = []
THREADING_LIMIT = 10
started_threads = queue.Queue(maxsize=1000000)
not_started_threads = queue.Queue(maxsize=1000000)
elastic_search = None


def get_data(asin):
    current_product = get_the_product(asin)
    if current_product:
        products.append(current_product)
        print(current_product['asin'])
        json_data = json.dumps(current_product, indent=4, sort_keys=False)
        elastic_search.index(index="amazon", doc_type="product-title", id=asin, body=json_data)


def get_path_of_chrome_driver():
    path = os.path.join( os.getcwd() + "/webdriver", "chromedriver")
    if _platform == "linux" or _platform == "linux2":
        # linux
        path += "_linux"
    elif _platform == "darwin":
        # MAC OS X
        path += "_mac"
    elif _platform == "win32" or _platform == "win64":
        # Windows
        path += "_win"
    return path


def get_driver():
    options = Options()
    # options.add_argument('--proxy-server=' + Proxy.get_proxy())
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--no-zygote')
    # options.add_argument("window-size=1024,768")
    driver = webdriver.Chrome(executable_path=get_path_of_chrome_driver(), chrome_options=options)
    # driver = webdriver.Chrome(get_path_of_chrome_driver())
    # driver.find_element_by_tag_name()
    return driver


def get_images(driver):
    images = []
    try:
        image_div = driver.find_element_by_id("altImages")
    except Exception as e:
        try:
            image_div = driver.find_element_by_id("imageBlockThumbs")
        except Exception as e2:
            e = e2
            return images

    for image in image_div.find_elements_by_tag_name("img"):
        if image.get_attribute('src').endswith(".jpg"):
            image_src = image.get_attribute('src').split(".")
            image_src[len(image_src)-2] = "_UL900_"
            images.append(".".join(image_src))

    return images


def get_price(driver):
    if not driver.find_elements_by_id("priceblock_ourprice"):
        price_str = driver.find_elements_by_id("priceblock_ourprice").text.strip()
        price_str = price_str.replace("$", "")
        try:
            price = float(price_str.split(" ")[0])
            price = price * 100.0
            return price
        except Exception as e:
            return ""

    elif not driver.find_elements_by_id("price_inside_buybox"):
        price_str = driver.find_elements_by_id(id="price_inside_buybox").text.strip()
        price_str = price_str.replace("$", "")
        try:
            price = float(price_str.split(" ")[0])
            price = price * 100.0
            return price
        except Exception as e:
            return ""
    else:
        prices = driver.find_elements_by_class_name("a-color-price")
        price_str = prices[1].text.strip()
        try:
            price_str = price_str.replace("$", "")
            price = float(price_str.split(" ")[0])
            price = price * 100.0
            return price
        except Exception as e:
            ""


def get_the_product(asin):
    print(asin)
    url = PRODUCT_URL + asin
    driver = get_driver()
    try:
        driver.get(url)
        curr_product = {}
        curr_product['asin'] = asin
        curr_product['title'] = driver.find_element_by_id("productTitle").text
        # curr_product['price'] = get_price(driver)
        # curr_product['images'] = get_images(driver)
        #
        # flg = True
        # for key, value in curr_product.items():
        #     if value is None or not value or value == "None":
        #         flg = False
        #         break
        #     elif type(value) == str and len(value) == 0:
        #         flg = False
        #         break

        driver.quit()
        # if not flg:
        #     return

        return curr_product
    except Exception as e:
        print("Not found product " + asin)
        print(e)


def search_page_scrape(starting, ending, url):
    print(starting, ending, url)
    driver = get_driver()
    driver.get(url)

    if driver.find_elements_by_id("noResultsTitle"):
        driver.quit()
        return

    ind = starting
    while ind < ending:
        try:
            result_id = "result_" + str(ind)
            ele = driver.find_element_by_id(result_id)
            asin = ele.get_attribute('data-asin')

            process = Process(target=get_data, args=(asin,))
            processes.append(process)

            ind += 1
        except Exception as e:
            ind += 1
    return


def give_a_search(search_text):
    print(search_text)
    counter = 1
    url = SEARCH_URL + search_text
    pageNo = 1
    while pageNo < 40:
        full_url = url+"&page="+str(pageNo)
        print(full_url)
        process = Process(target=search_page_scrape, args=(counter, counter+40, full_url))
        processes.append(process)
        counter += 30
        pageNo += 1


def solve():
    for src in search_fields:
        process = Process(target=give_a_search, args=(src,))
        processes.append(process)

    for index, process in enumerate(processes):
        process.start()

        if index == len(processes) - 1:
            time.sleep(random.randint(1,4))

    for process in processes:
        process.join()


if __name__ == "__main__":
    elastic_search = ElasticSearch.connect_elasticsearch()
    if elastic_search is not None:
        solve()
        print("len ", len(products))
