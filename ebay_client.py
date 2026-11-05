import base64
import requests
from config import EBAY_BROWSE_URL, EBAY_OAUTH_URL, EBAY_SANDBOX_APP_ID, EBAY_SANDBOX_CERT_ID


def get_sandbox_token():
  if not EBAY_SANDBOX_APP_ID or not EBAY_SANDBOX_CERT_ID:
    print("Error: Sandbox App ID or Cert ID missing from environment.")
    return None

  credentials = f"{EBAY_SANDBOX_APP_ID}:{EBAY_SANDBOX_CERT_ID}"
  encoded_creds = base64.b64encode(credentials.encode()).decode()

  headers = {
      "Authorization": f"Basic {encoded_creds}",
      "Content-Type": "application/x-www-form-urlencoded",
  }

  payload = {
      "grant_type": "client_credentials",
      "scope": "https://api.ebay.com/oauth/api_scope",
  }

  response = requests.post(EBAY_OAUTH_URL, headers=headers, data=payload)

  if response.status_code == 200:
    return response.json().get("access_token")
  else:
    print(f"Token Error: {response.status_code} - {response.text}")
    return None


def search_ebay_listings(
    query=(
        "2024 Topps Chrome Shohei Ohtani Refractor -PSA -BGS -SGC -CGC -Base"
        " -Lot -Reprint -Graded"
    ),
    max_price=75,
):
  token = get_sandbox_token()
  if not token:
    return []

  headers = {
      "Authorization": f"Bearer {token}",
      "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
  }

  params = {"q": query, "limit": 20, "filter": f"price:[..{max_price}]"}

  response = requests.get(EBAY_BROWSE_URL, headers=headers, params=params)

  if response.status_code == 200:
    data = response.json()
    items = data.get("itemSummaries", [])
    parsed_items = []
    for item in items:
      parsed_items.append({
          "item_id": item.get("itemId"),
          "title": item.get("title"),
          "price": float(item.get("price", {}).get("value", 0)),
          "url": item.get("itemWebUrl"),
          "image_url": item.get("image", {}).get("imageUrl"),
      })
    return parsed_items
  else:
    print(f"Search Error: {response.status_code} - {response.text}")
    return []
