from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def find(self, locator):
        return self.wait.until(
            EC.element_to_be_clickable(locator)
        )

    def click(self, locator):
        element = self.find(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def type(self, locator, text):
        self.find(locator).send_keys(text)

    def scroll_down(self):
        self.driver.execute_script("window.scrollBy(0, 500);")