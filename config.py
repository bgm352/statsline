import os
from dotenv import load_dotenv

load_dotenv()

# eBay Sandbox API Configuration
EBAY_SANDBOX_APP_ID = os.getenv("EBAY_SANDBOX_APP_ID")
EBAY_SANDBOX_CERT_ID = os.getenv("EBAY_SANDBOX_CERT_ID")
EBAY_SANDBOX_DEV_ID = os.getenv("EBAY_SANDBOX_DEV_ID")

# Sandbox Gateway URLs
EBAY_OAUTH_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
EBAY_BROWSE_URL = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
