import streamlit as st
import json
import os
from datetime import datetime
import subprocess

st.set_page_config(page_title="Upcoming Games", layout="wide")
st.title("📂 Upcoming Games")

# Load projected pitchers
projected_pitchers = []
if os.path.exists("data/projected_pitchers_today.json"):
    with open("data/projected_pitchers_today.json", "r") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                projected_pitchers = [entry for entry in data if isinstance(entry, dict)]
        except Exception as e:
            st.error(f"Error loading projected pitchers: {e}")

# Display upcoming games with projected pitchers
for entry in projected_pitchers:
    away = entry.get("away_team", "TBD")
    home = entry.get("home_team", "TBD")
    away_pitcher = entry.get("away_pitcher", "TBD")
    home_pitcher = entry.get("home_pitcher", "TBD")
    game_time = entry.get("game_time", "TBD")

    with st.container():
        st.markdown(f"**{away} @ {home}** 🕒 {game_time}")
        st.markdown(f"**Top1:** {away_pitcher} vs. {home_pitcher}")
        st.markdown(f"**Bot1:** {home_pitcher} vs. {away_pitcher}")
        st.markdown("---")

# Add refresh button at the bottom
st.markdown("---")
if st.button("🔁 Refresh Starters (Projected Pitchers)"):
    with st.spinner("Updating projected pitchers..."):
        try:
            result = subprocess.run([
                "python", "update_starred_pitchers.py"
            ], capture_output=True, text=True, check=True)
            st.success("✅ Projected pitchers updated!")
            st.code(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error("❌ Failed to update projected pitchers.")
            st.code(e.stderr)
