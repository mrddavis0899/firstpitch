import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import time
import os
import json
from unidecode import unidecode

st.set_page_config(page_title="Live Tracker", layout="wide")
st.title("🔴 Live First Pitch Leadoff Tracker")

# Load target hitters from session
def normalize(name):
    return unidecode(name).lower().strip()

target_hitters = st.session_state.get("target_hitters", set())
normalized_targets = {normalize(name) for name in target_hitters}

# Store fired alerts
if "alerts_fired" not in st.session_state:
    st.session_state.alerts_fired = set()

# Load or initialize pinned alerts from JSON
ALERTS_FILE = "data/pinned_alerts.json"
os.makedirs("data", exist_ok=True)
if os.path.exists(ALERTS_FILE):
    with open(ALERTS_FILE, "r") as f:
        st.session_state.pinned_alerts = json.load(f)
else:
    st.session_state.pinned_alerts = []

# Persist refresh rate
if "refresh_rate" not in st.session_state:
    st.session_state.refresh_rate = 60

refresh_rate = st.sidebar.slider(
    "🔁 Refresh Frequency (seconds)", 15, 120, st.session_state.refresh_rate, 15
)
st.session_state.refresh_rate = refresh_rate

# Clear pinned alerts
if st.sidebar.button("🗑️ Clear Pinned Alerts"):
    st.session_state.pinned_alerts = []
    with open(ALERTS_FILE, "w") as f:
        json.dump([], f)

# Eastern time label
eastern = pytz.timezone("US/Eastern")
st.caption(f"🕒 Last Checked: {datetime.now(eastern).strftime('%I:%M %p').lstrip('0')} (ET)")

# Get live MLB games
def get_live_games():
    now = datetime.now(eastern)
    target_date = (now - pd.Timedelta(days=1)).strftime("%Y-%m-%d") if now.hour < 4 else now.strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}&hydrate=team,linescore"
    r = requests.get(url)
    data = r.json()
    return data["dates"][0].get("games", []) if data.get("dates") else []

games = get_live_games()
live_games = [g for g in games if g.get("status", {}).get("detailedState") == "In Progress"]
debug_blocks = []
alerts = []
leadoff_memory = {}  # Track preserved leadoff hitters after 2 outs

for game in live_games:
    game_id = game["gamePk"]
    linescore = game.get("linescore", {})
    is_top = linescore.get("isTopInning", True)
    outs = linescore.get("outs", 0)
    inning = linescore.get("currentInning", 0)
    side = "away" if is_top else "home"
    team_name = game["teams"][side]["team"]["name"]

    boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    boxscore = requests.get(boxscore_url).json()
    team_data = boxscore["teams"][side]
    players = team_data["players"]
    batters = team_data["batters"]

    feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
    feed = requests.get(feed_url).json()
    play = feed.get("liveData", {}).get("plays", {}).get("currentPlay", {})
    batter_id = play.get("matchup", {}).get("batter", {}).get("id")

    if batter_id not in batters:
        continue

    # Filter out pitchers
    valid_batters = [b for b in batters if players.get(f"ID{b}", {}).get("person", {}).get("primaryPosition", {}).get("code") != "P"]
    if not valid_batters:
        continue

    current_index = valid_batters.index(batter_id) if batter_id in valid_batters else -1
    current_name = players.get(f"ID{batter_id}", {}).get("person", {}).get("fullName", "❓ Unknown")

    block_lines = [f"<strong>🧠 {team_name} - Inning {inning} ({'Top' if is_top else 'Bottom'}), Outs: {outs}</strong>",
                   f"Current Batter: {current_name} (Index {current_index})"]

    # Always determine next batter
    next_index = (valid_batters.index(batter_id) + 1) % len(valid_batters)
    next_id = valid_batters[next_index]
    next_name = players.get(f"ID{next_id}", {}).get("person", {}).get("fullName", "❓ Unknown")

    leadoff_memory[game_id] = {
        "id": next_id,
        "name": next_name
    }

    if outs < 3:
        block_lines.append(f"⏭️ Projected Leadoff Next Inning: {next_name}")
    else:
        leadoff_info = leadoff_memory.get(game_id)
        leadoff_name = leadoff_info["name"] if leadoff_info else next_name
        block_lines.append(f"<span style='color:red; font-weight:bold;'>⏭️ Leadoff Next Inning (locked): {leadoff_name}</span>")

        if normalize(leadoff_name) in normalized_targets:
            alert_key = (game_id, inning + 1, leadoff_name)
            if alert_key not in st.session_state.alerts_fired:
                st.session_state.alerts_fired.add(alert_key)
                detected_time = datetime.now(eastern).strftime('%I:%M %p').lstrip('0')
                alert = {
                    "Batter": leadoff_name,
                    "Team": team_name,
                    "Will Lead Off Inning": inning + 1,
                    "Detected At": detected_time
                }
                alerts.append(alert)
                st.session_state.pinned_alerts.append(alert)
                with open(ALERTS_FILE, "w") as f:
                    json.dump(st.session_state.pinned_alerts, f, indent=2)

    debug_blocks.append(block_lines)

# Show new alerts
if alerts:
    st.subheader("🚨 Leadoff Alert: Target Hitter Leading Off Next Inning")
    for alert in alerts:
        msg = f"**🧨 {alert['Batter']}** from the **{alert['Team']}** will lead off the **{alert['Will Lead Off Inning']}** inning. ⏰ Detected at **{alert['Detected At']}**."
        st.markdown(f"""
        <div style='background-color:#ff6347; color:white; padding:15px; border-radius:10px; font-weight:bold;'>
            {msg}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No target hitters currently set to lead off next inning.")

# Show pinned alerts
if st.session_state.pinned_alerts:
    with st.expander("📌 Pinned Alerts"):
        st.dataframe(pd.DataFrame(st.session_state.pinned_alerts))

# Show debug info with outlined blocks (vertical layout)
with st.expander("🔍 Live Game Status"):
    for block in debug_blocks:
        html = "<div style='border:2px solid #ccc; padding:10px; border-radius:10px; margin-bottom:10px;'>"
        for line in block:
            html += f"<div style='margin-bottom:4px'>{line}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

# Refresh
time.sleep(refresh_rate)
st.rerun()
