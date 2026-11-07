from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):
    PRODUCT = (By.XPATH, "//img[@src='assets/img/products/pliers01.avif']")

    def __init__(self, driver):
        super().__init__(driver)

    def click_product(self):
        self.click(self.PRODUCT)