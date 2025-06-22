import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
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

    # 🔒 Only include MLB regular season and playoff games
    df = df[df["game_type"].isin(["R", "F", "L", "D"])]
    
    # Get the current date and the date 7 days ago
    today = datetime.today()
    seven_days_ago = today - timedelta(days=7)
    
    # Filter data to include only the last 7 days of games
    df = df[df["game_date"] >= seven_days_ago]

    # Filter to the first pitch of each at-bat
    df = df[df["pitch_number"] == 1]

    # Filter to ensure the player has at least 2 ABs per game
    df["ab_count"] = df.groupby(['batter_name', 'game_date'])['pitch_type'].transform('count')
    
    # Relax the AB filtering condition: Allow 1 AB per game but require at least 4 games in the last 7 days
    hitter_ab_count = df.groupby(['batter_name', 'game_date'])['ab_count'].count()
    
    # Adjust condition: players must appear in at least 4 of the last 7 games and have 1 AB per game
    valid_hitters = hitter_ab_count.groupby('batter_name').filter(lambda x: len(x) >= 4 and all(x >= 1))

    # Filter df to only include valid hitters
    df_valid_hitters = df[df['batter_name'].isin(valid_hitters.index)]

    # DEBUG: Inspect unique values in 'description' and 'events' columns to check if they contain expected values
    st.write("Unique values in 'description' column:")
    st.write(df_valid_hitters['description'].unique())

    st.write("Unique values in 'events' column:")
    st.write(df_valid_hitters['events'].unique())

    # Simplify success criteria: Consider any value in 'description' or 'events' as success (non-null check)
    df_valid_hitters["success"] = df_valid_hitters["description"].notnull() | df_valid_hitters["events"].notnull()

    # Check the 'success' column after simplifying criteria
    st.write("Rows with 'success' column (after broadening success criteria):")
    st.write(df_valid_hitters[['batter_name', 'game_date', 'description', 'events', 'success']].head(10))  # Show first 10 rows

    # Summarize by batter
    summary = df_valid_hitters.groupby("batter_name").agg(
        total_pas=("pitch_type", "count"),
        successes=("success", "sum")
    ).reset_index()

    # Print out the summary of successes
    st.write("Summary of successes per player:")
    st.write(summary)

    # Only consider hitters with at least 2 successes
    hot_hitters = summary[summary["successes"] >= 2].sort_values("successes", ascending=False).head(5)

    # Check if hot_hitters has any data
    if not hot_hitters.empty:
        st.subheader("🔥 Hot Hitters – Last 7 Days (First Pitch Only)")
        st.dataframe(hot_hitters.rename(columns={
            "batter_name": "Player",
            "total_pas": "First Pitch PAs",
            "successes": "In-Play/Hit Outcomes"
        }), hide_index=True, use_container_width=True)
    else:
        st.subheader("🔥 Hot Hitters")
        st.info("No hot hitters found in the last 7 days based on current first-pitch stats.")
