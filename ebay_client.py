import os
import requests
from bs4 import BeautifulSoup

class eBayClient:
    def __init__(self):
        # Optional: Add eBay API OAuth tokens here if upgrading to official Finding API later
        pass

    def fetch_listing_data(self, listing_url: str) -> dict:
        """
        Scrapes or extracts title, image URL, and buy-it-now price 
        directly from a live eBay listing URL.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            resp = requests.get(listing_url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 1. Extract Title
            title_tag = soup.find("h1", class_="x-item-title__mainTitle")
            title = title_tag.get_text(strip=True) if title_tag else "Unknown Card Listing"

            # Clean up eBay's awkward span prefix if present
            if title.startswith("Details about  "):
                title = title.replace("Details about  ", "", 1)

            # 2. Extract Primary Image URL
            image_tag = soup.find("div", class_="ux-image-carousel-item") or soup.find("img", class_="ux-image-zoom__image")
            image_url = ""
            if image_tag:
                img_el = image_tag.find("img")
                if img_el and img_el.has_attr("src"):
                    image_url = img_el["src"]
                elif img_el and img_el.has_attr("data-src"):
                    image_url = img_el["data-src"]

            # Fallback for standard OpenGraph image tag
            if not image_url:
                og_img = soup.find("meta", property="og:image")
                if og_img:
                    image_url = og_img.get("content", "")

            # 3. Extract Price
            price_tag = soup.find("div", class_="x-price-primary") or soup.find("span", class_="ux-textspans")
            raw_price = 25.0 # Default fallback
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                # Clean string like "$25.00" -> 25.0
                cleaned_price = ''.join(c for c in price_text if c.isdigit() or c == '.')
                if cleaned_price:
                    try:
                        raw_price = float(cleaned_price)
                    except ValueError:
                        pass

            return {
                "status": "success",
                "title": title,
                "image_url": image_url,
                "raw_price": raw_price
            }

        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
                "title": "",
                "image_url": "",
                "raw_price": 25.0
            }
