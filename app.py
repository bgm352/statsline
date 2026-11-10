import os
import streamlit as st
from dotenv import load_dotenv
from vision_screener import VisionScreener
from roi_calculator import ROICalculator
from ebay_client import eBayClient

load_dotenv()
st.set_page_config(page_title="Statsline | Arbitrage Engine", layout="wide")

screener = VisionScreener(max_ratio=55.0)
ebay = eBayClient()

st.sidebar.title("Statsline Settings")
grading_fee = st.sidebar.number_input("PSA Grading Fee ($)", value=25.0, step=1.0)
inbound_ship = st.sidebar.number_input("Inbound Shipping ($)", value=4.50, step=0.5)
return_ship = st.sidebar.number_input("Allocated Return Ship/Ins ($)", value=5.50, step=0.5)
gem_prob = st.sidebar.slider("Baseline Gem Rate Probability", 0.10, 0.95, 0.65, 0.05)

calculator = ROICalculator(grading_fee=grading_fee, inbound_shipping=inbound_ship, grading_shipping_ins=return_ship)

st.title("Statsline: Fully Automated Arbitrage Engine")

# Single Input Point: Just paste the live listing link
listing_url = st.text_input("Paste eBay Listing URL for Automatic Ingestion", placeholder="https://www.ebay.com/itm/...")

col1, col2 = st.columns([1, 1])

# State variables for auto-populated fields
auto_title = ""
auto_image = ""
auto_price = 25.0

if listing_url and "ebay.com" in listing_url:
    with st.spinner("Auto-extracting listing metadata & image from eBay..."):
        scraped = ebay.fetch_listing_data(listing_url)
        if scraped["status"] == "success":
            auto_title = scraped["title"]
            auto_image = scraped["image_url"]
            auto_price = scraped["raw_price"]
            st.success("Successfully ingested listing data automatically!")
        else:
            st.warning(f"Could not auto-scrape URL completely: {scraped.get('reason')}")

with col1:
    st.subheader("1. Automated Ingestion & Comps")
    card_title = st.text_input("Card Title / Player", value=auto_title)
    image_url = st.text_input("Card Image URL (Auto-Fetched)", value=auto_image)

    c1, c2, c3 = st.columns(3)
    raw_price = c1.number_input("Raw Buy Price ($)", min_value=1.0, value=auto_price, step=1.0)
    psa10_comp = c2.number_input("PSA 10 Comp ($)", min_value=1.0, value=300.0, step=5.0)
    psa9_comp = c3.number_input("PSA 9 Comp ($)", min_value=0.0, value=85.0, step=5.0)

    run_analysis = st.button("Run Automated Triage", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Triage Verdict & Metrics")
    if run_analysis:
        roi_data = calculator.evaluate_deal(raw_price, psa10_comp, psa9_comp, gem_prob)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("All-In Cost", f"${roi_data['all_in_cost']}")
        m2.metric("PSA 10 Net Profit", f"${roi_data['psa10_profit']}", f"{roi_data['psa10_roi_pct']}% ROI")
        m3.metric("PSA 9 Net Profit", f"${roi_data['psa9_profit']}")
        m4.metric("Expected Value (EV)", f"${roi_data['expected_profit_ev']}", f"{roi_data['expected_roi_pct']}% EV ROI")
        
        st.divider()
        
        if image_url.strip():
            vision_data = screener.evaluate_from_url(image_url.strip())
            if vision_data["status"] == "success":
                v1, v2, v3 = st.columns(3)
                v1.metric("L/R Ratio", vision_data["lr_ratio_str"], "PASS" if vision_data["passes_lr"] else "FAIL")
                v2.metric("T/B Ratio", vision_data["tb_ratio_str"], "PASS" if vision_data["passes_tb"] else "FAIL")
                v3.metric("Vision Gate", "GEM CANDIDATE" if vision_data["is_gem_candidate"] else "REJECT")
            else:
                st.warning(f"Vision Notice: {vision_data.get('reason')}")
            st.image(image_url, width=260, caption="Auto-Ingested Listing Image")
