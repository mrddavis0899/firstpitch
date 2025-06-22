import streamlit as st
import os  # <-- Import the os module here
from mlb_first_pitch import get_hot_hitters  # Import the function from mlb_first_pitch.py

# Automatically update games_today.csv on app startup
if not os.path.exists("games_today.csv") or os.stat("games_today.csv").st_size == 0:
    with st.spinner("📅 Pulling today's MLB games..."):
        from update_games_and_pitchers import update_csvs
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

# Call the get_hot_hitters function to retrieve the hot hitters
hot_hitters = get_hot_hitters()

if hot_hitters is not None:
    if not hot_hitters.empty:
        st.subheader("🔥 Hot Hitters – Last 5 Games (First Pitch Only)")
        st.dataframe(hot_hitters.rename(columns={
            "batter_name": "Player",
            "total_pas": "First Pitch PAs",
            "successes": "In-Play/Hit Outcomes"
        }), hide_index=True, use_container_width=True)
    else:
        st.subheader("🔥 Hot Hitters")
        st.info("No hot hitters found in the last 5 games based on current first-pitch stats.")
else:
    st.error("First-pitch data not found. Please ensure the dataset is available.")
