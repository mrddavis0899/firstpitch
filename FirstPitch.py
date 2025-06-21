import streamlit as st
import pandas as pd
import os
from datetime import datetime
from update_games_and_pitchers import update_csvs

# Automatically update games_today.csv on app startup
if not os.path.exists("games_today.csv") or os.stat("games_today.csv").st_size == 0:
    with st.spinner("📅 Pulling today's MLB games..."):
        update_csvs()
        st.success("✅ Updated today's games.")

# Navigation landing page
st.set_page_config(page_title="FirstPitch", layout="wide")

st.title("⚾️ FirstPitch Home")
st.markdown("""
Welcome to **FirstPitch** — your MLB real-time tracker and trend analyzer for first-pitch betting.
- Use the **Live Tracker** tab to catch when your target hitters are leading off next.
- The **Trend Explorer** helps you find hot hitters by filtering swing rates, contact %, and more.
- In **Upcoming Games**, find matchups where hitters face favorable pitchers on the first pitch.
""")
