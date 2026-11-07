from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class Product_Control(BasePage):

    Product_Detail_Control = (By.ID, "lblCartCount")
    Product_Detail = (By.XPATH, "//strong[text()='Toplam']")
    Cart_Quantity = (By.CSS_SELECTOR, "input[id^='quantity-']")
    Proceed_To_Checkout = (By.CSS_SELECTOR, "[data-test='proceed-1']")


    def __init__(self, driver):
        super().__init__(driver)

    def get_product_control(self):
        self.click(self.Product_Detail_Control)

    def get_product_detail(self):
        return self.find(self.Product_Detail).is_displayed()

    def get_cart_quantity(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.Cart_Quantity)
        ).get_attribute("value")

    def proceed_to_checkout(self):
        self.click(self.Proceed_To_Checkout)
