import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import time

st.set_page_config(page_title="Live Tracker", layout="wide")
st.title("🔴 Live First Pitch Leadoff Tracker")

# Load target hitters from session
target_hitters = st.session_state.get("target_hitters", set())
normalized_targets = {name.lower() for name in target_hitters}

# Track already alerted combos
if "alerts_fired" not in st.session_state:
    st.session_state.alerts_fired = set()

# Store pinned alerts
if "pinned_alerts" not in st.session_state:
    st.session_state.pinned_alerts = []

# Persist refresh rate across pages
if "refresh_rate" not in st.session_state:
    st.session_state.refresh_rate = 60  # default value

refresh_rate = st.sidebar.slider(
    "🔁 Refresh Frequency (seconds)",
    min_value=15,
    max_value=120,
    value=st.session_state.refresh_rate,
    step=15
)
st.session_state.refresh_rate = refresh_rate

# Timestamp
eastern = pytz.timezone("US/Eastern")
st.caption(f"🕒 Last Checked: {datetime.now(eastern).strftime('%I:%M %p').lstrip('0')} (ET)")

# Pull live schedule data
def get_live_games():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore"
    r = requests.get(url)
    return r.json().get("dates", [])[0].get("games", [])

games = get_live_games()
alerts = []
debug_lines = []

for game in games:
    game_id = game.get("gamePk")
    status = game.get("status", {}).get("detailedState")
    if status != "In Progress":
        continue

    linescore = game.get("linescore", {})
    is_top = linescore.get("isTopInning", True)
    outs = linescore.get("outs", 0)
    inning = linescore.get("currentInning")

    batting_side = "away" if is_top else "home"
    fielding_side = "home" if is_top else "away"
    batting_team = game.get("teams", {}).get(batting_side, {}).get("team", {}).get("name", "")

    # 📦 Get boxscore to map player IDs to names
    boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    boxscore = requests.get(boxscore_url).json()
    team_box = boxscore.get("teams", {}).get(batting_side, {})
    batters = team_box.get("batters", [])
    players = team_box.get("players", {})

    # 🔄 Get live play-by-play feed
    feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
    feed = requests.get(feed_url).json()
    live_play = feed.get("liveData", {}).get("plays", {}).get("currentPlay", {})
    matchup = live_play.get("matchup", {})
    current_batter_id = matchup.get("batter", {}).get("id")

    try:
        current_index = batters.index(current_batter_id)
    except:
        current_index = 0

    player_key = f"ID{current_batter_id}"
    current_batter_name = players.get(player_key, {}).get("person", {}).get("fullName", f"❓ Unknown - ID: {current_batter_id}")

    debug_lines.append(f"🧠 {batting_team} - Inning {inning} ({'Top' if is_top else 'Bottom'}), Outs: {outs}")
    debug_lines.append(f"   Current Batter: {current_batter_name} (Index {current_index})")

    if current_index + 1 < len(batters):
        next_batter_id = batters[current_index + 1]
    else:
        next_batter_id = batters[0]  # wrap around

    next_player_key = f"ID{next_batter_id}"
    next_batter_name = players.get(next_player_key, {}).get("person", {}).get("fullName", f"❓ Unknown - ID: {next_batter_id}")
    debug_lines.append(f"   Next Batter: {next_batter_name}")

    if next_batter_name.lower() in normalized_targets:
        debug_lines.append(f"   🎯 {next_batter_name} is a TARGET!")

    # 🔁 NEW logic: if batting team just made 3rd out, check who will lead off next inning
    if outs == 3:
        leadoff_index = (current_index + 1) % len(batters)
        leadoff_id = batters[leadoff_index]
        leadoff_key = f"ID{leadoff_id}"
        leadoff_name = players.get(leadoff_key, {}).get("person", {}).get("fullName", f"❓ Unknown - ID: {leadoff_id}")

        debug_lines.append(f"   ⏭️ Leadoff Next Inning: {leadoff_name}")

        if leadoff_name.lower() in normalized_targets:
            alert_key = (game_id, inning + 1, leadoff_name)
            if alert_key not in st.session_state.alerts_fired:
                st.session_state.alerts_fired.add(alert_key)
                detected_time = datetime.now(eastern).strftime('%I:%M %p').lstrip('0')
                alert = {
                    "Batter": leadoff_name,
                    "Team": batting_team,
                    "Will Lead Off Inning": inning + 1,
                    "Detected At": detected_time
                }
                alerts.append(alert)
                st.session_state.pinned_alerts.append(alert)

# Show alerts
if alerts:
    st.subheader("🚨 Leadoff Alert: Target Hitter Leading Off Next Inning")
    st.table(pd.DataFrame(alerts))
else:
    st.info("No target hitters currently set to lead off next inning.")

# Pinned alerts section
if st.session_state.pinned_alerts:
    st.subheader("📌 Pinned Alerts")
    st.table(pd.DataFrame(st.session_state.pinned_alerts))

# Show diagnostics
with st.expander("🔍 Debug Mode: Show Game State"):
    for line in debug_lines:
        st.write(line)
    st.write("\n🧪 Batters list:")
    st.write(batters)
    st.write("\n🧪 Players dictionary keys:")
    st.json(list(players.keys())[:10])

# Auto-refresh
time.sleep(refresh_rate)
st.rerun()
