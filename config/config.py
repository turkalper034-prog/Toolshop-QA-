import os
from urllib.parse import urlparse


BASE_URL = os.getenv(
    "TOOLSHOP_BASE_URL",
    "https://practicesoftwaretesting.com",
).rstrip("/")
LIVE_MODE = os.getenv("TOOLSHOP_LIVE_MODE", "").strip().casefold() in {
    "1",
    "true",
    "yes",
}
IS_DEMO_SITE = urlparse(BASE_URL).hostname == "practicesoftwaretesting.com"