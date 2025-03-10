import csv
import logging
import sys
from dataclasses import fields, dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

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


def write_products_to_csv(products: [Product], filename: str):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products():
    """
    Main function that scrapes products from all specified pages and writes them into separate CSV files.
    """
    # Dictionary with page URLs and corresponding CSV filenames
    pages = {
        HOME_URL: "home.csv",
        COMPUTERS_URL: "computers.csv",
        LAPTOPS_URL: "laptops.csv",
        TABLETS_URL: "tablets.csv",
        PHONES_URL: "phones.csv",
        TOUCH_URL: "touch.csv"
    }

    for url, csv_filename in pages.items():
        print(f"Scraping products for URL: {url}")
        # Open the corresponding page
        _driver.get(url)
        time.sleep(2)  # Allow page to load

        # Collect all products
        products = []
        if url in {LAPTOPS_URL, TABLETS_URL, TOUCH_URL}:
            # Handle pagination (pages with "More" button)
            while True:
                products.extend(scrape_products_from_page())
                try:
                    # Look for the "More" button and click it
                    more_button = _driver.find_element(By.CLASS_NAME, ".row ecomerce-items ecomerce-items-more")
                    ActionChains(_driver).move_to_element(more_button).click().perform()
                    time.sleep(3)  # Wait for new products to load
                except:
                    # If "More" button is not found, we've reached the last page
                    break
        else:
            # Handle single page scraping
            products.extend(scrape_products_from_page())

        # Write collected products to CSV
        write_products_to_csv(products, csv_filename)
        print(f"{len(products)} products saved to {csv_filename}")


def scrape_products_from_page():
    products = []
    product_elements = _driver.find_elements(By.CLASS_NAME,
                                             "thumbnail")  # Assuming products are within elements of this class

    for product_element in product_elements:
        try:
            title = product_element.find_element(By.CLASS_NAME, "title").text.strip()
            description = product_element.find_element(By.CLASS_NAME, "description").text
            price = float(product_element.find_element(By.CLASS_NAME, "price").text.strip()[1:])  # Remove "$" sign
            rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
            rating = len(rating_element.find_elements(By.CLASS_NAME, "span"))  # Count star icons
            num_of_reviews = int(rating_element.find_element(By.TAG_NAME, "p").text.strip().split(" ")[0])

            # Create a Product instance
            product = Product(
                title=title, description=description, price=price,
                rating=rating, num_of_reviews=num_of_reviews
            )
            products.append(product)

        except Exception as e:
            print(f"Error parsing product: {e}")

    return products


def main():
    # Ensure the driver is set up properly
    with webdriver.Chrome() as driver:
        set_driver(driver)  # Set the driver globally
        get_all_products()  # Start scraping


if __name__ == "__main__":
    main()
