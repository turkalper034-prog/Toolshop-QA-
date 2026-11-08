import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from config.config import IS_DEMO_SITE
from pages.login_page import LoginPage
from pages.product_basket_page import BasketPage


API_BASE_URL = "https://api.practicesoftwaretesting.com"
TEST_CASE_ID = "TC-CART-UIAPI-001"


def _get_json(url):
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read()
    except HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        if error.code == 429 or error.code >= 500:
            pytest.skip(
                f"API environment returned HTTP {error.code} for {url}: "
                f"{response_body}"
            )
        pytest.fail(
            f"API returned HTTP {error.code} for {url}: {response_body}",
            pytrace=False,
        )
    except (URLError, TimeoutError, socket.timeout) as error:
        pytest.skip(f"API connection/environment error for {url}: {error}")

    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        pytest.fail(f"API returned invalid JSON for {url}: {error}", pytrace=False)


@pytest.mark.case_id(TEST_CASE_ID)
def test_TC_CART_UIAPI_001_ui_cart_matches_api_cart(driver, report_step):
    if not IS_DEMO_SITE:
        pytest.skip("UI/API cart integration requires the configured demo site.")

    products_url = f"{API_BASE_URL}/products"
    product_list = _get_json(products_url)
    products = product_list.get("data") if isinstance(product_list, dict) else None
    report_step(
        "GET products and select an available item",
        "HTTP 200 product list with at least one in-stock product",
        f"{products_url}; product list received={isinstance(products, list)}",
        "PASS" if isinstance(products, list) else "FAIL",
    )
    assert isinstance(products, list), (
        f"Expected product list from {products_url}, "
        f"got {type(products).__name__}."
    )

    product = next(
        (
            item
            for item in products
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("in_stock") is True
        ),
        None,
    )
    if product is None:
        report_step(
            "Check product availability",
            "At least one API product has in_stock=true",
            "No in-stock products returned; no cart action attempted",
            "SKIP",
        )
        pytest.skip("No in-stock products are available; no cart action was attempted.")

    product_id = product["id"]
    detail_url = f"{API_BASE_URL}/products/{product_id}"
    api_product = _get_json(detail_url)
    valid_product = (
        isinstance(api_product, dict)
        and api_product.get("id") == product_id
        and isinstance(api_product.get("in_stock"), bool)
    )
    report_step(
        "Confirm selected product availability",
        f"Product {product_id} exists and API in_stock=true",
        f"API in_stock={api_product.get('in_stock') if isinstance(api_product, dict) else 'missing'}",
        "PASS" if valid_product and api_product["in_stock"] else "FAIL",
    )
    assert valid_product, (
        f"Unexpected product detail response from {detail_url}: {api_product!r}"
    )
    if not api_product["in_stock"]:
        pytest.skip(
            f"Product {product_id} became unavailable; no cart action was attempted."
        )

    LoginPage(driver).click_product_by_id(product_id)
    product_page = BasketPage(driver)
    assert product_page.get_product_name(), (
        f"Product detail page for {product_id} did not load."
    )
    assert driver.current_url.rstrip("/").endswith(f"/product/{product_id}"), (
        f"UI opened unexpected product URL: {driver.current_url}"
    )

    ui_stock = product_page.get_stock_status()
    report_step(
        "Check UI availability before adding",
        "Product is in stock and add-to-cart is enabled",
        f"UI in_stock={ui_stock}",
        "PASS" if ui_stock is True else "SKIP" if ui_stock is False else "FAIL",
    )
    if ui_stock is False:
        pytest.skip(
            f"UI reports product {product_id} out of stock; no cart action was attempted."
        )
    assert ui_stock is True, (
        f"UI could not confirm product {product_id} is available."
    )

    existing_cart_id = product_page.get_cart_id()
    if existing_cart_id:
        pytest.skip(
            "Browser already has a cart session; refusing to alter pre-existing cart data."
        )

    stock_message = product_page.click_add_to_cart_page()
    if stock_message:
        report_step(
            "Add product through UI",
            "In-stock product is added to the browser cart",
            f"UI returned stock notice: {stock_message}",
            "SKIP",
        )
        pytest.skip(
            f"UI reported product unavailable; cart was not modified: {stock_message}"
        )

    try:
        cart_id = WebDriverWait(driver, 15).until(
            lambda current_driver: product_page.get_cart_id() or False
        )
    except TimeoutException:
        report_step(
            "Read browser cart session",
            "UI stores cart_id after adding the product",
            "No cart_id appeared in sessionStorage",
            "FAIL",
        )
        pytest.fail(
            "UI add-to-cart did not create a browser cart session.",
            pytrace=False,
        )

    ui_quantity = product_page.get_cart_quantity_from_session()
    report_step(
        "Add product through UI",
        f"Browser cart contains product {product_id} with quantity 1",
        f"sessionStorage cart_id={cart_id}; cart_quantity={ui_quantity}",
        "PASS" if ui_quantity == "1" else "FAIL",
    )
    assert ui_quantity == "1", (
        f"Expected one product in the browser cart, got {ui_quantity!r}."
    )

    cart_url = f"{API_BASE_URL}/carts/{cart_id}"
    api_cart = _get_json(cart_url)
    cart_shape_valid = (
        isinstance(api_cart, dict)
        and api_cart.get("id") == cart_id
        and isinstance(api_cart.get("cart_items"), list)
    )
    report_step(
        "GET browser cart through API",
        f"GET {cart_url} returns the same cart id and an item list",
        (
            f"cart id={api_cart.get('id')}; "
            f"cart_items type={type(api_cart.get('cart_items')).__name__}"
            if isinstance(api_cart, dict)
            else f"Unexpected response type: {type(api_cart).__name__}"
        ),
        "PASS" if cart_shape_valid else "FAIL",
    )
    assert cart_shape_valid, (
        f"Unexpected cart response from {cart_url}: {api_cart!r}"
    )

    cart_item = next(
        (
            item
            for item in api_cart["cart_items"]
            if isinstance(item, dict) and item.get("product_id") == product_id
        ),
        None,
    )
    api_quantity = cart_item.get("quantity") if cart_item else None
    report_step(
        "Compare browser and API cart contents",
        f"Product {product_id} appears in API cart with quantity {ui_quantity}",
        f"API product_id={cart_item.get('product_id') if cart_item else 'missing'}; "
        f"API quantity={api_quantity}",
        "PASS" if cart_item and api_quantity == int(ui_quantity) else "FAIL",
    )
    assert cart_item is not None, (
        f"Product {product_id} added in UI is missing from API cart {cart_id}."
    )
    assert isinstance(api_quantity, int) and not isinstance(api_quantity, bool), (
        f"API cart quantity has unexpected value: {api_quantity!r}"
    )
    assert api_quantity == int(ui_quantity), (
        f"Cart quantity differs: browser={ui_quantity}, API={api_quantity}."
    )
