import pandas as pd
import streamlit as st
from database import DB_NAME, init_db
import sqlite3

st.set_page_config(
    page_title="Armor OS Arbitrage Desk", page_icon="⚾", layout="wide"
)

st.title("⚾ Armor OS | Automated Arbitrage Desk")
st.markdown("### Sandbox Scraper & Human-in-the-Loop Verification Queue")

init_db()


def load_candidates():
  conn = sqlite3.connect(DB_NAME)
  df = pd.read_sql_query("SELECT * FROM candidates", conn)
  conn.close()
  return df


df_candidates = load_candidates()

if df_candidates.empty:
  st.info(
      "No candidates in local database yet. Run your eBay search script to"
      " populate items."
  )
else:
  st.dataframe(df_candidates[["title", "price", "opencv_status", "url"]])
