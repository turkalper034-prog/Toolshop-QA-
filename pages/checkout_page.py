from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    GUEST_TAB = (By.CSS_SELECTOR, "a[href='#guest-tab']")
    GUEST_EMAIL = (By.ID, "guest-email")
    GUEST_FIRST_NAME = (By.ID, "guest-first-name")
    GUEST_LAST_NAME = (By.ID, "guest-last-name")
    GUEST_SUBMIT = (By.CSS_SELECTOR, "[data-test='guest-submit']")
    GUEST_CONTINUE = (By.CSS_SELECTOR, "[data-test='proceed-2-guest']")
    COUNTRY = (By.ID, "country")
    POSTAL_CODE = (By.ID, "postal_code")
    HOUSE_NUMBER = (By.ID, "house_number")
    STREET = (By.ID, "street")
    CITY = (By.ID, "city")
    STATE = (By.ID, "state")
    ADDRESS_CONTINUE = (By.CSS_SELECTOR, "[data-test='proceed-3']")
    PAYMENT_METHOD = (By.ID, "payment-method")
    CARD_NUMBER = (By.ID, "credit_card_number")
    CARD_EXPIRATION = (By.ID, "expiration_date")
    CARD_CVV = (By.ID, "cvv")
    CARD_HOLDER = (By.ID, "card_holder_name")
    FINISH = (By.CSS_SELECTOR, "[data-test='finish']")

    def start_guest_checkout(self, email, first_name, last_name):
        self.click(self.GUEST_TAB)
        self.type(self.GUEST_EMAIL, email)
        self.type(self.GUEST_FIRST_NAME, first_name)
        self.type(self.GUEST_LAST_NAME, last_name)
        self.click(self.GUEST_SUBMIT)
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"), f"{first_name} {last_name}"
            )
        )
        self.click(self.GUEST_CONTINUE)

    def enter_billing_address(self, postal_code, house_number):
        self.wait.until(EC.visibility_of_element_located(self.COUNTRY))
        Select(self.driver.find_element(*self.COUNTRY)).select_by_value("US")
        self.type(self.POSTAL_CODE, postal_code)
        self.type(self.HOUSE_NUMBER, house_number)
        self.wait.until(
            lambda driver: all(
                driver.find_element(*locator).get_attribute("value")
                for locator in (self.STREET, self.CITY, self.STATE)
            )
        )
        self.click(self.ADDRESS_CONTINUE)
        return self.wait.until(EC.visibility_of_element_located(self.PAYMENT_METHOD))

    def enter_test_card(self, card_number, expiration, cvv, card_holder):
        payment_method = self.wait.until(
            EC.visibility_of_element_located(self.PAYMENT_METHOD)
        )
        Select(payment_method).select_by_value("credit-card")
        self.type(self.CARD_NUMBER, card_number)
        self.type(self.CARD_EXPIRATION, expiration)
        self.type(self.CARD_CVV, cvv)
        self.type(self.CARD_HOLDER, card_holder)

    def submit_payment(self):
        self.click(self.FINISH)
        return self.wait.until(
            lambda driver: "Payment was successful"
            if "Payment was successful" in driver.find_element(By.TAG_NAME, "body").text
            else False
        )

    def get_order_confirmation(self):
        return self.wait.until(
            lambda driver: self._order_confirmation_text(driver)
        )

    def confirm_order(self):
        self.click(self.FINISH)
        return self.get_order_confirmation()

    @staticmethod
    def _order_confirmation_text(driver):
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "Siparişiniz için teşekkürler!" in body_text and "INV-" in body_text:
            return body_text
        return False
