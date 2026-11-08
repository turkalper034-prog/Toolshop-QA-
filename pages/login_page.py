from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):
    PRODUCT_IMAGE_FILE = "pliers01.avif"
    PRODUCT = (By.XPATH, f"//img[@src='assets/img/products/{PRODUCT_IMAGE_FILE}']")

    def __init__(self, driver):
        super().__init__(driver)

    def click_product(self):
        self.click(self.PRODUCT)

    def click_product_by_id(self, product_id):
        self.click((By.CSS_SELECTOR, f"[data-test='product-{product_id}']"))