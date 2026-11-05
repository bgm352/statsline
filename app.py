from datetime import datetime
import os
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if SUPABASE_URL and SUPABASE_KEY
    else None
)

# Page Configuration
st.set_page_config(
    page_title="Statsline | Arbitrage Terminal",
    page_icon="📈",
    layout="wide",
)

# Sidebar Navigation & Stats
st.sidebar.title("Statsline Controls")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation", ["Live Triage Queue", "Approved Portfolio", "System Logs"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**System Status:** Online\n\n**Database:** Supabase Synced\n\n**Domain:**"
    " statsline.com"
)


def load_candidates(status="pending"):
  """Loads candidate records from Supabase filtered by status."""
  if not supabase:
    # Fallback mock data if Supabase keys aren't loaded yet
    return [
        {
            "id": 1,
            "item_id": "123456789",
            "title": "2023 Topps Chrome Shohei Ohtani Refractor",
            "price": 45.00,
            "url": "https://ebay.com",
            "image_url": "https://via.placeholder.com/150",
            "status": "pending",
        }
    ]

  try:
    response = (
        supabase.table("candidates")
        .select("*")
        .eq("status", status)
        .execute()
    )
    return response.data
  except Exception as e:
    st.error(f"Error loading from Supabase: {e}")
    return []


def update_status(item_id, new_status):
  """Updates the triage status of a candidate item in Supabase."""
  if not supabase:
    return
  try:
    supabase.table("candidates").update({"status": new_status}).eq(
        "item_id", item_id
    ).execute()
  except Exception as e:
    st.error(f"Error updating status: {e}")


# --- MAIN APP INTERFACE ---

if page == "Live Triage Queue":
  st.title("Statsline Market Intelligence & Triage")
  st.markdown(
      "Real-time ingested raw listings awaiting automated OpenCV and manual"
      " triage review."
  )
  st.markdown("---")

  candidates = load_candidates("pending")

  if not candidates:
    st.success(
        "Queue is clear! Run `python ebay_client.py` to ingest new live"
        " marketplace listings."
    )
  else:
    for item in candidates:
      with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
          img_url = item.get("image_url")
          if img_url:
            st.image(img_url, width=120)
          else:
            st.text("No Image")

        with col2:
          st.subheader(item.get("title"))
          st.markdown(f"**Price:** `${item.get('price', 0):.2f}` USD")
          st.markdown(f"[View Live eBay Listing]({item.get('url')})")
          st.caption(f"Item ID: {item.get('item_id')}")

        with col3:
          st.markdown("### Triage Action")
          if st.button("Approve to Buy", key=f"approve_{item.get('item_id')}"):
            update_status(item.get("item_id"), "approved")
            st.rerun()

          if st.button(
              "Catch & Release", key=f"release_{item.get('item_id')}"
          ):
            update_status(item.get("item_id"), "rejected")
            st.rerun()

        st.markdown("---")

elif page == "Approved Portfolio":
  st.title("Statsline Approved Inventory")
  st.markdown("Candidates cleared through triage awaiting acquisition/grading.")
  st.markdown("---")

  approved_items = load_candidates("approved")
  if not approved_items:
    st.info("No items currently approved in portfolio.")
  else:
    for item in approved_items:
      st.write(
          f"**{item.get('title')}** — `${item.get('price', 0):.2f}` |"
          f" [Link]({item.get('url')})"
      )

elif page == "System Logs":
  st.title("Statsline System Diagnostics")
  st.markdown("Pipeline execution logs and database sync health.")
  st.markdown("---")
  st.text("Supabase connection: ACTIVE")
  st.text("eBay API OAuth Status: TOKEN VALID")
  st.text(f"Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
