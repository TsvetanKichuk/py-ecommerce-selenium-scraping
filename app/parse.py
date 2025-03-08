import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import Tag, BeautifulSoup
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
PHONES_URL = urljoin(HOME_URL, "phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets/")
TOUCH_URL = urljoin(PHONES_URL, "touch/")

_driver: WebDriver = None

def get_driver() -> WebDriver:
    return _driver

def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parse.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def parce_hdd_block_prices(product_soup: Tag) -> dict:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".row ecommerce-items ecommerce-items more"))
    driver = get_driver()
    driver.get(absolute_url)
    swatches = driver.find_elements(By.CLASS_NAME, "swatches")
    buttons = driver.find_element(By.TAG_NAME, "button")
    prices = {}
    for button in buttons:
        if  not button.get_property("disabled"):
            button.click()
            prices[button.get_property("value")] = float(
                driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
            )
    driver.close()
    return prices

def parse_single_product(product: Tag) -> Product:
    hdd_prices = parce_hdd_block_prices(product)
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
        additional_info={"hdd_prices": hdd_prices}
    )

def get_home_products() -> [Product]:
    text = requests.get(HOME_URL).content
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".row ecommerce-items ecommerce-items more")
    return [parse_single_product(product) for product in products]

def get_num_pages(page_soup: Tag) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return int(pagination.select("li")[-2].text)

def single_page_laptops(soup: Tag) -> [Product]:
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]

def get_laptops() -> [Product]:
    logging.info("Getting laptops...")
    text = requests.get(LAPTOPS_URL).content
    first_page_soup = BeautifulSoup(text, "html.parser")
    all_products = single_page_laptops(first_page_soup)
    num_pages = get_num_pages(first_page_soup)
    for page_num in range(2, num_pages + 1):
        logging.info(f"start parsing page {page_num}")
        text = requests.get(LAPTOPS_URL, {"page": page_num}).content
        next_page_soup = BeautifulSoup(text, "html.parser")
        all_products.extend(single_page_laptops(next_page_soup))
    return all_products


def write_products_to_csv(products: [Product]):
    with open("results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(products) for products in products])



def get_all_products() -> None:
    pass

def main():
    with webdriver.Chrome() as driver:
        set_driver(driver)
        write_products_to_csv(get_all_products())


if __name__ == "__main__":
    get_home_products()
