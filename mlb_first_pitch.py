import os
import pandas as pd
import streamlit as st

# Function to get Hot Hitters
def get_hot_hitters():
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

        # Return hot hitters
        return hot_hitters
    else:
        st.error("First-pitch data not found. Please ensure the dataset is available.")
        return None
