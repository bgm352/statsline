import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Armor OS Arbitrage Desk", page_icon="⚾", layout="wide"
)

st.title("⚾ Armor OS | Automated Arbitrage Desk")
st.markdown("### Sandbox Scraper & Human-in-the-Loop Verification Queue")

# Absolute path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "armor_os.db")


def load_candidates():
  if not os.path.exists(DB_NAME):
    return pd.DataFrame(), "Database file not found at path."

  conn = sqlite3.connect(DB_NAME)
  try:
    df = pd.read_sql_query("SELECT * FROM candidates", conn)
    conn.close()
    return df, None
  except Exception as e:
    conn.close()
    return pd.DataFrame(), str(e)


df_candidates, error_msg = load_candidates()

if error_msg:
  st.error(f"Database Error: {error_msg}")
elif df_candidates.empty:
  st.warning(
      f"Database connected successfully at `{DB_NAME}`, but the `candidates`"
      " table is currently empty."
  )
  if st.button("Insert Test Row"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
            INSERT OR IGNORE INTO candidates (item_id, title, price, url, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (
        "TEST-123",
        "2024 Topps Chrome Shohei Ohtani Refractor #1",
        49.99,
        "https://sandbox.ebay.com",
        "https://via.placeholder.com/150",
    ))
    conn.commit()
    conn.close()
    st.rerun()
else:
  st.success(f"Loaded {len(df_candidates)} candidates from database.")
  st.dataframe(
      df_candidates[
          [
              "item_id",
              "title",
              "price",
              "opencv_status",
              "review_status",
              "url",
          ]
      ]
  )
