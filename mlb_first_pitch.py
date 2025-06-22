import os
import pandas as pd
import streamlit as st

# Load the data from your existing dataset (you already have this from Trend Explorer)
CSV_FILE = "first_pitch_data_2025.csv"

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    df["game_date"] = pd.to_datetime(df["game_date"])

    # Filter to only first-pitch events
    df = df[df["pitch_number"] == 1]

    # Focus on batters only by excluding pitchers (assuming 'stand' indicates batting)
    df = df[df["stand"].notnull()]

    # Filter successful first-pitch outcomes (ball, single, double, home run, etc.)
    successful_outcomes = ['ball', 'single', 'double', 'triple', 'home_run', 'hit_into_play']
    df_successful = df[df['events'].isin(successful_outcomes)]

    # Filter to include only the last 5 games for each player (if you have the game date and batter name)
    df['rank'] = df.groupby('batter_name')['game_date'].rank(method="first", ascending=False)
    df_recent = df[df['rank'] <= 5]

    # Count successful outcomes per batter
    summary = df_recent.groupby("batter_name").agg(
        total_pas=("pitch_type", "count"),
        successes=("events", lambda x: (x.isin(successful_outcomes)).sum())
    ).reset_index()

    # Filter players who have at least 2 successful outcomes
    hot_hitters = summary[summary["successes"] >= 2]

    # Show hot hitters
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
