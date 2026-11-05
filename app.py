import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client
from vision_screener import VisionScreener
from roi_calculator import ROICalculator

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

st.set_page_config(page_title="Statsline | Arbitrage Engine", layout="wide")

@st.cache_resource
def init_supabase() -> Client | None:
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()
screener = VisionScreener(max_ratio=55.0)

# Sidebar Configuration for Global Grading & Fee Assumptions
st.sidebar.title("Statsline Settings")
st.sidebar.subheader("Grading & Fee Parameters")
grading_fee = st.sidebar.number_input("PSA Grading Fee ($)", value=25.0, step=1.0)
inbound_ship = st.sidebar.number_input("Inbound Shipping ($)", value=4.50, step=0.5)
return_ship = st.sidebar.number_input("Allocated Return Ship/Ins ($)", value=5.50, step=0.5)
gem_prob = st.sidebar.slider("Baseline Gem Rate Probability", 0.10, 0.95, 0.65, 0.05)

calculator = ROICalculator(
    grading_fee=grading_fee,
    inbound_shipping=inbound_ship,
    grading_shipping_ins=return_ship
)

st.title("Statsline: Raw-to-Graded Arbitrage Engine")
st.markdown("Automated OpenCV 55/45 pre-screening and fee-adjusted Expected Value (EV) triage.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Candidate Input")
    card_title = st.text_input("Card Title / Player", placeholder="2025 Bowman Chrome Cooper Flagg RC")
    listing_url = st.text_input("eBay Listing URL", placeholder="https://www.ebay.com/itm/...")
    image_url = st.text_input("Direct Card Image URL (for OpenCV Check)", placeholder="https://i.ebayimg.com/images/...")

    c1, c2, c3 = st.columns(3)
    with c1:
        raw_price = st.number_input("Raw Buy Price ($)", min_value=1.0, value=25.0, step=1.0)
    with c2:
        psa10_comp = st.number_input("PSA 10 Comp ($)", min_value=1.0, value=300.0, step=5.0)
    with c3:
        psa9_comp = st.number_input("PSA 9 Comp ($)", min_value=0.0, value=85.0, step=5.0)

    run_analysis = st.button("Run Statsline Triage", type="primary", use_container_width=True)

with col2:
    st.subheader("2. Triage Verdict & Metrics")
    if run_analysis:
        # Run Financial Math
        roi_data = calculator.evaluate_deal(
            raw_price=raw_price,
            psa10_comp=psa10_comp,
            psa9_comp=psa9_comp,
            gem_probability=gem_prob
        )

        # Run OpenCV Centering Check if image URL is provided
        vision_data = {"status": "skipped", "lr_ratio_str": "N/A", "tb_ratio_str": "N/A", "is_gem_candidate": False}
        if image_url.strip():
            with st.spinner("Running OpenCV contour & border analysis..."):
                vision_data = screener.evaluate_from_url(image_url.strip())

        # Display Financial Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("All-In Cost", f"${roi_data['all_in_cost']}")
        m2.metric("PSA 10 Net Profit", f"${roi_data['psa10_profit']}", f"{roi_data['psa10_roi_pct']}% ROI")
        m3.metric("PSA 9 Net Profit", f"${roi_data['psa9_profit']}")
        m4.metric("Expected Value (EV)", f"${roi_data['expected_profit_ev']}", f"{roi_data['expected_roi_pct']}% EV ROI")

        st.divider()

        # Display OpenCV Vision Results
        st.markdown("**OpenCV Centering Gate (<= 55/45 Target)**")
        if vision_data["status"] == "success":
            v1, v2, v3 = st.columns(3)
            v1.metric("Left / Right Ratio", vision_data["lr_ratio_str"], "PASS" if vision_data["passes_lr"] else "FAIL")
            v2.metric("Top / Bottom Ratio", vision_data["tb_ratio_str"], "PASS" if vision_data["passes_tb"] else "FAIL")
            v3.metric("Vision Gate", "GEM CANDIDATE" if vision_data["is_gem_candidate"] else "REJECT")
        elif vision_data["status"] == "manual_review_needed":
            st.warning(f"Manual Slider Check Required: {vision_data['reason']}")
        elif vision_data["status"] == "error":
            st.error(f"Image Fetch Error: {vision_data['reason']}")
        else:
            st.info("No image URL provided. Financial triage only.")

        if image_url.strip():
            st.image(image_url, caption="Evaluated Listing Image", width=280)

        # Save to Supabase Queue
        if supabase and st.button("Save Target to Supabase Queue"):
            payload = {
                "card_title": card_title,
                "listing_url": listing_url,
                "image_url": image_url,
                "raw_price": raw_price,
                "all_in_cost": roi_data["all_in_cost"],
                "psa10_comp": psa10_comp,
                "psa10_profit": roi_data["psa10_profit"],
                "expected_profit_ev": roi_data["expected_profit_ev"],
                "lr_centering": vision_data.get("lr_ratio_str", "N/A"),
                "tb_centering": vision_data.get("tb_ratio_str", "N/A"),
                "vision_status": vision_data.get("status", "manual")
            }
            try:
                supabase.table("arbitrage_candidates").insert(payload).execute()
                st.success("Saved to Supabase `arbitrage_candidates` table!")
            except Exception as e:
                st.error(f"Database Save Error: {e}")
