import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
import os

try:
    st.title("📅 Upcoming MLB Games")

    # Check for valid games_today.csv
    if not os.path.exists("games_today.csv") or os.path.getsize("games_today.csv") == 0:
        st.error("❌ games_today.csv is missing or empty. Run the app when games are scheduled.")
        st.stop()

    games = pd.read_csv("games_today.csv")
    if games.empty:
        st.warning("🕐 No games found for today or games_today.csv is empty.")
        st.stop()

    # Detect game time column
    time_col = next((col for col in games.columns if "time" in col.lower()), None)
    if time_col is None:
        st.error("❌ No column containing 'time' found in games_today.csv.")
        st.write("Available columns:", list(games.columns))
        st.stop()

    # Convert game time to Eastern
    eastern = pytz.timezone("US/Eastern")
    games["StartTimeET"] = pd.to_datetime(games[time_col], errors='coerce', utc=True).dt.tz_convert(eastern)

    # Load pitcher data with safety checks
    if not os.path.exists("starting_pitchers.csv") or os.path.getsize("starting_pitchers.csv") == 0:
        st.warning("⚠️ No starting_pitchers.csv found or file is empty. Pitcher data will be skipped.")
        pitchers = pd.DataFrame(columns=["Pitcher", "Zone%", "FPO%", "xBA"])
    else:
        pitchers = pd.read_csv("starting_pitchers.csv")

    # Ensure proper types
    for col in ["home_pitcher", "away_pitcher"]:
        if col in games.columns:
            games[col] = games[col].astype(str)
    if not pitchers.empty and "Pitcher" in pitchers.columns:
        pitchers["Pitcher"] = pitchers["Pitcher"].astype(str)

    # Merge pitcher stats
    if not pitchers.empty:
        games = games.merge(pitchers, how="left", left_on="home_pitcher", right_on="Pitcher", suffixes=("", "_home"))
        games = games.merge(pitchers, how="left", left_on="away_pitcher", right_on="Pitcher", suffixes=("", "_away"))

    # Filter upcoming and live games
    now = datetime.now(tz=eastern)
    upcoming_games = games[games["StartTimeET"] > now].copy()
    live_games = games[games["StartTimeET"] <= now].copy()

    # Display upcoming games
    st.subheader("Upcoming Games Today")
    if not upcoming_games.empty:
        show_cols = ["StartTimeET", "home_team", "away_team", "home_pitcher", "away_pitcher"]
        if all(col in upcoming_games.columns for col in show_cols):
            styled = upcoming_games[show_cols].style
            st.dataframe(styled, use_container_width=True)
        else:
            st.dataframe(upcoming_games.head(), use_container_width=True)
    else:
        st.info("✅ No upcoming games remaining today.")

    # Optional: Show live games
    if not live_games.empty:
        st.subheader("Live or Completed Games")
        st.dataframe(live_games[["StartTimeET", "home_team", "away_team"]], use_container_width=True)

except Exception as e:
    st.error(f"🚨 Unexpected error: {e}")
