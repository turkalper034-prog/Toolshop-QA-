from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class BasketPage(BasePage):
    add_basket_page = (By.ID, "btn-increase-quantity")
    add_to_cart_page = (By.ID, "btn-add-to-cart")
    specs_title = (By.XPATH, "//h3[@data-test='specs-title']")
    stock_notifications = (By.CSS_SELECTOR, "[role='alert']")

    def __init__(self, driver):
        super().__init__(driver)

    def _get_stock_notification(self):
        stock_phrases = (
            "stokta yok",
            "stok yok",
            "tükendi",
            "out of stock",
            "not in stock",
        )
        page_text = self.driver.find_element(By.TAG_NAME, "body").text.casefold()
        for phrase in stock_phrases:
            if phrase in page_text:
                return phrase

        for notification in self.driver.find_elements(*self.stock_notifications):
            message = notification.text.strip()
            if notification.is_displayed() and any(
                phrase in message.casefold() for phrase in stock_phrases
            ):
                return message
        return None

    def _wait_for_stock_notification(self):
        try:
            return WebDriverWait(self.driver, 2).until(
                lambda driver: self._get_stock_notification() or False
            )
        except TimeoutException:
            return None

    def _click_or_get_stock_notification(self, locator):
        def action_or_notification(driver):
            message = self._get_stock_notification()
            if message:
                return ("notification", message)

            element = EC.element_to_be_clickable(locator)(driver)
            if element:
                return ("element", element)
            return False

        action, value = self.wait.until(action_or_notification)
        if action == "notification":
            return value

        self.driver.execute_script("arguments[0].click();", value)
        return self._wait_for_stock_notification()

    def click_add_basket_page(self):
        return self._click_or_get_stock_notification(self.add_basket_page)

    def click_add_to_cart_page(self):
        return self._click_or_get_stock_notification(self.add_to_cart_page)

    def get_specs_title(self):
        return self.find(self.specs_title).is_displayed()
