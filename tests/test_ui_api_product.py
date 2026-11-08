import json
import socket
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pytest

from config.config import IS_DEMO_SITE
from pages.login_page import LoginPage
from pages.product_basket_page import BasketPage


API_BASE_URL = "https://api.practicesoftwaretesting.com"
TEST_CASE_ID = "TC-UIAPI-001"


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
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        pytest.fail(f"API returned invalid JSON for {url}: {error}", pytrace=False)
    return payload


@pytest.mark.case_id(TEST_CASE_ID)
def test_TC_UIAPI_001_product_details_match_between_api_and_ui(driver, report_step):
    if not IS_DEMO_SITE:
        pytest.skip("UI/API integration requires the configured demo site.")

    list_url = f"{API_BASE_URL}/products"
    product_list = _get_json(list_url)
    products = product_list.get("data") if isinstance(product_list, dict) else None
    report_step(
        "GET product list",
        "HTTP 200 JSON object containing a product list",
        f"{list_url}; data type={type(products).__name__}",
        "PASS" if isinstance(products, list) else "FAIL",
    )
    assert isinstance(products, list), (
        f"Expected a product list from {list_url}, got {type(products).__name__}."
    )

    product = next(
        (
            item
            for item in products
            if isinstance(item, dict)
            and isinstance(item.get("product_image"), dict)
            and item["product_image"].get("file_name")
            == LoginPage.PRODUCT_IMAGE_FILE
        ),
        None,
    )
    report_step(
        "Select the POM product",
        f"API product image {LoginPage.PRODUCT_IMAGE_FILE}",
        f"Product found: {product.get('id') if product else 'no'}",
        "PASS" if product else "FAIL",
    )
    assert product, (
        f"No product with image {LoginPage.PRODUCT_IMAGE_FILE} was returned "
        f"by {list_url}."
    )

    product_id = product.get("id")
    assert isinstance(product_id, str) and product_id, (
        f"API product did not contain a valid id: {product!r}"
    )
    detail_url = f"{API_BASE_URL}/products/{product_id}"
    api_product = _get_json(detail_url)
    api_fields_valid = (
        isinstance(api_product, dict)
        and api_product.get("id") == product_id
        and isinstance(api_product.get("name"), str)
        and bool(api_product["name"].strip())
        and isinstance(api_product.get("price"), (int, float))
        and not isinstance(api_product.get("price"), bool)
        and isinstance(api_product.get("in_stock"), bool)
    )
    api_report_fields = (
        {
            key: api_product.get(key)
            for key in ("id", "name", "price", "in_stock")
        }
        if isinstance(api_product, dict)
        else api_product
    )
    if isinstance(api_report_fields, dict):
        image = api_product.get("product_image")
        api_report_fields["product_image"] = (
            image.get("file_name") if isinstance(image, dict) else None
        )
    report_step(
        "GET product details",
        "HTTP 200 with matching id, name, price, and in_stock fields",
        json.dumps(api_report_fields, ensure_ascii=False, sort_keys=True),
        "PASS" if api_fields_valid else "FAIL",
    )
    assert api_fields_valid, (
        f"Unexpected product detail response from {detail_url}: {api_product!r}"
    )

    LoginPage(driver).click_product()
    product_page = BasketPage(driver)
    ui_name = product_page.get_product_name()
    ui_price = Decimal(product_page.get_unit_price())
    api_price = Decimal(str(api_product["price"]))
    ui_url = driver.current_url
    expected_path = f"/product/{product_id}"
    actual_path = urlparse(ui_url).path.rstrip("/")
    report_step(
        "Open matching product in the UI",
        f"{expected_path} showing {api_product['name']}",
        f"{ui_url}; UI name={ui_name}",
        "PASS" if actual_path == expected_path else "FAIL",
    )
    assert actual_path == expected_path, (
        f"UI opened {ui_url}, expected product path {expected_path}."
    )

    report_step(
        "Compare product name",
        api_product["name"],
        ui_name,
        "PASS" if ui_name == api_product["name"] else "FAIL",
    )
    assert ui_name == api_product["name"], (
        f"Product name differs: API={api_product['name']!r}, UI={ui_name!r}."
    )

    report_step(
        "Compare product price",
        str(api_price),
        str(ui_price),
        "PASS" if ui_price == api_price else "FAIL",
    )
    assert ui_price == api_price, (
        f"Product price differs: API={api_price}, UI={ui_price}."
    )

    ui_in_stock = product_page.get_stock_status()
    stock_matches = ui_in_stock is not None and ui_in_stock == api_product["in_stock"]
    ui_stock_text = (
        "in stock"
        if ui_in_stock
        else "out of stock"
        if ui_in_stock is False
        else "unknown"
    )
    report_step(
        "Compare stock status",
        f"API in_stock={api_product['in_stock']}",
        f"UI status={ui_stock_text}; API in_stock={api_product['in_stock']}",
        "PASS" if stock_matches else "FAIL",
    )
    assert ui_in_stock is not None, (
        "UI stock status could not be determined from the availability text "
        "or add-to-cart button."
    )
    assert ui_in_stock == api_product["in_stock"], (
        f"Stock status differs: API in_stock={api_product['in_stock']}, "
        f"UI in_stock={ui_in_stock}."
    )
