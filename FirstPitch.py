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

# Add Hot Hitters section to home page
CSV_FILE = "first_pitch_data_2025.csv"

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df[df["pitch_number"] == 1]

    # 🔒 Only include MLB regular season and playoff games
    df = df[df["game_type"].isin(["R", "F", "L", "D"])]

    # Filter to last 5 games per hitter
    df["rank"] = df.groupby("batter_name")["game_date"].rank(method="first", ascending=False)
    df_recent = df[df["rank"] <= 5]

    df_recent["success"] = df_recent["description"].isin(["hit_into_play"]) | \
                             df_recent["events"].isin(["single", "double", "triple", "home_run"])

    summary = df_recent.groupby("batter_name").agg(
        total_pas=("pitch_type", "count"),
        successes=("success", "sum")
    ).reset_index()

    hot_hitters = summary[summary["successes"] >= 3].sort_values("successes", ascending=False).head(5)

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
