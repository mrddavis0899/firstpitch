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

# Use Eastern Time
eastern = pytz.timezone("US/Eastern")
st.caption(f"🕒 Last Checked: {datetime.now(eastern).strftime('%I:%M %p').lstrip('0')} (ET)")

# Pull live schedule data (with after-midnight support)
def get_live_games():
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)

    # If it's after midnight but before 4am, pull yesterday's games
    if now.hour < 4:
        target_date = (now - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        target_date = now.strftime("%Y-%m-%d")

    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}&hydrate=team,linescore"
    r = requests.get(url)
    data = r.json()
    if not data.get("dates"):
        return []
    return data["dates"][0].get("games", [])

games = get_live_games()
alerts = []
debug_lines = []
batters = None
players = {}

# Show all game statuses
for g in games:
    away = g.get("teams", {}).get("away", {}).get("team", {}).get("name", "Away")
    home = g.get("teams", {}).get("home", {}).get("team", {}).get("name", "Home")
    status = g.get("status", {}).get("detailedState", "Unknown")
    debug_lines.append(f"📋 {away} vs {home} — Status: {status}")

# Filter in-progress games
live_games = [g for g in games if g.get("status", {}).get("detailedState") == "In Progress"]
debug_lines.append(f"📊 Found {len(games)} games today, {len(live_games)} currently In Progress.")

for game in live_games:
    game_id = game.get("gamePk")
    linescore = game.get("linescore", {})
    is_top = linescore.get("isTopInning", True)
    outs = linescore.get("outs", 0)
    inning = linescore.get("currentInning")

    batting_side = "away" if is_top else "home"
    batting_team = game.get("teams", {}).get(batting_side, {}).get("team", {}).get("name", "")

    # Boxscore
    boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    boxscore = requests.get(boxscore_url).json()
    team_box = boxscore.get("teams", {}).get(batting_side, {})
    batters = team_box.get("batters", [])
    players = team_box.get("players", {})

    if not batters:
        debug_lines.append(f"⚠️ No batters found for {batting_team}")
    if not players:
        debug_lines.append(f"⚠️ No players data for {batting_team}")

    # Live play-by-play
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

    # ✅ Always check who is due to lead off next inning (now or soon)
    leadoff_index = (current_index + (1 if outs >= 3 else 0)) % len(batters)
    leadoff_id = batters[leadoff_index]
    leadoff_key = f"ID{leadoff_id}"
    leadoff_name = players.get(leadoff_key, {}).get("person", {}).get("fullName", f"❓ Unknown - ID: {leadoff_id}")

    debug_lines.append(f"   ⏭️ Leadoff Next Inning: {leadoff_name}")

    if leadoff_name.lower() in normalized_targets:
        alert_key = (game_id, inning + (1 if outs >= 3 else 0), leadoff_name)
        if alert_key not in st.session_state.alerts_fired:
            st.session_state.alerts_fired.add(alert_key)
            detected_time = datetime.now(eastern).strftime('%I:%M %p').lstrip('0')
            alert = {
                "Batter": leadoff_name,
                "Team": batting_team,
                "Will Lead Off Inning": inning + (1 if outs >= 3 else 0),
                "Detected At": detected_time
            }
            alerts.append(alert)
            st.session_state.pinned_alerts.append(alert)

    # For completeness: show next batter as well
    if current_index + 1 < len(batters):
        next_batter_id = batters[current_index + 1]
    else:
        next_batter_id = batters[0]
    next_player_key = f"ID{next_batter_id}"
    next_batter_name = players.get(next_player_key, {}).get("person", {}).get("fullName", f"❓ Unknown - ID: {next_batter_id}")
    debug_lines.append(f"   Next Batter: {next_batter_name}")

    if next_batter_name.lower() in normalized_targets:
        debug_lines.append(f"   🎯 {next_batter_name} is a TARGET!")

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

# Debug section
with st.expander("🔍 Debug Mode: Show Game State"):
    if debug_lines:
        for line in debug_lines:
            st.write(line)
    else:
        st.write("ℹ️ No debug information available yet.")

    st.write("\n🧪 Batters list:")
    if batters:
        st.write(batters)
    else:
        st.write("⚠️ No batters found — possibly an issue with API response.")

    st.write("\n🧪 Players dictionary keys:")
    if players:
        st.json(list(players.keys())[:10])
    else:
        st.write("⚠️ No player data — possibly an issue with API response.")

# Auto-refresh
time.sleep(refresh_rate)
st.rerun()
