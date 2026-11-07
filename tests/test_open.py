
import pytest

from config.config import IS_DEMO_SITE, LIVE_MODE
from pages.checkout_page import CheckoutPage
from pages.product_basket_page import BasketPage
from pages.login_page import LoginPage
from pages.product_control import Product_Control


@pytest.mark.smoke
@pytest.mark.regression
def test_product_cart_and_checkout_flow(driver):
    login_page = LoginPage(driver)
    login_page.click_product()

    product_basket_page = BasketPage(driver)
    assert product_basket_page.get_specs_title(), "Ürün detay sayfası açılmadı."

    stock_message = product_basket_page.click_add_basket_page()
    if stock_message:
        reason = f"[STOKTA YOK] Ürün sepete eklenemedi: {stock_message}"
        print("\n" + "=" * 64)
        print(f"STOK DURUMU: {reason}")
        print("Bu bir test hatası değil; stok olmadığı için sepet akışı atlandı.")
        print("=" * 64)
        pytest.skip(reason)

    stock_message = product_basket_page.click_add_to_cart_page()
    if stock_message:
        reason = f"[STOKTA YOK] Ürün sepete eklenemedi: {stock_message}"
        print("\n" + "=" * 64)
        print(f"STOK DURUMU: {reason}")
        print("Bu bir test hatası değil; stok olmadığı için sepet akışı atlandı.")
        print("=" * 64)
        pytest.skip(reason)

    product_control = Product_Control(driver)
    product_control.get_product_control()
    assert product_control.get_product_detail(), "Sepet/toplam bilgisi açılmadı."
    assert product_control.get_cart_quantity() == "2", "Sepette ürün miktarı 2 değil."

    if LIVE_MODE or not IS_DEMO_SITE:
        pytest.skip(
            "Ürün ve sepet kontrolleri geçti; canlı modda veya demo dışı adreste "
            "checkout/ödeme adımları güvenlik için çalıştırılmadı."
        )

    product_control.proceed_to_checkout()
    checkout_page = CheckoutPage(driver)
    checkout_page.start_guest_checkout(
        email="qa.checkout@example.com",
        first_name="Taylor",
        last_name="Test",
    )
    payment_method = checkout_page.enter_billing_address(
        postal_code="95814",
        house_number="42",
    )
    assert payment_method.is_displayed(), "Ödeme adımı açılmadı."

    checkout_page.enter_test_card(
        card_number="4111-1111-1111-1111",
        expiration="12/2030",
        cvv="123",
        card_holder="Taylor Test",
    )
    assert checkout_page.find(checkout_page.FINISH).is_enabled(), \
        "Kart bilgileri girildi ancak ödeme butonu etkinleşmedi."

    payment_message = checkout_page.submit_payment()
    assert payment_message == "Payment was successful", "Ödeme başarı mesajı görüntülenmedi."

    confirmation = checkout_page.confirm_order()
    assert "Siparişiniz için teşekkürler!" in confirmation, "Sipariş onay mesajı görüntülenmedi."
    assert "INV-" in confirmation, "Sipariş faturası numarası görüntülenmedi."
