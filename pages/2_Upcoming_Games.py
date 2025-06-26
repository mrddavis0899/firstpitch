import streamlit as st
import requests
import json
from datetime import datetime
import pytz
from unidecode import unidecode

st.set_page_config(page_title="Upcoming Games", layout="wide")
st.title("📂 Upcoming Games")

@st.cache_data(ttl=3600)
def load_games():
    url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=" + datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d")
    res = requests.get(url).json()
    return res["dates"][0]["games"] if res["dates"] else []

@st.cache_data(ttl=3600)
def load_lineups():
    url = "https://statsapi.mlb.com/api/v1/game/linescore?sportId=1"
    return requests.get(url).json()

@st.cache_data(ttl=3600)
def get_last_5_lineups(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster"
    return requests.get(url).json()

def normalize(name):
    return unidecode(name or "").lower().strip()

# Load target hitters
try:
    with open("data/target_hitters.json") as f:
        target_hitters = json.load(f)
except FileNotFoundError:
    target_hitters = []

normalized_targets = {normalize(name) for name in target_hitters}

# Fallback logic to extract projected leadoff from past 5 lineups (mocked version for now)
def get_fallback_leadoff(team_id):
    # Ideally you'd parse recent lineups and return most common 1st batter
    # For now this just returns None to simulate logic stub
    return None

games = load_games()

st.markdown(f"⏰ Lineups last checked: {datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %I:%M:%S %p ET')}")

for game in games:
    status = game["status"]["detailedState"]
    if status not in ["Pre-Game", "Scheduled"]:
        continue

    away = game["teams"]["away"]["team"]["name"]
    home = game["teams"]["home"]["team"]["name"]
    away_id = game["teams"]["away"]["team"]["id"]
    home_id = game["teams"]["home"]["team"]["id"]

    try:
        away_pitcher = game["teams"]["away"]["probablePitcher"]["fullName"]
    except:
        away_pitcher = "TBD"
    try:
        home_pitcher = game["teams"]["home"]["probablePitcher"]["fullName"]
    except:
        home_pitcher = "TBD"

    # Use fallback method to determine projected leadoff
    away_leadoff = get_fallback_leadoff(away_id) or "TBD"
    home_leadoff = get_fallback_leadoff(home_id) or "TBD"

    def highlight(name):
        if normalize(name) in normalized_targets:
            return f"<span style='color:red; font-weight:bold;'>🎯 {name}</span>"
        return name

    game_time = datetime.strptime(game["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
    game_time_et = game_time.astimezone(pytz.timezone("US/Eastern")).strftime("%I:%M %p ET")

    st.markdown(f"""
    <div style='padding: 12px 20px; border: 1px solid #ccc; border-radius: 8px; margin-bottom: 20px;'>
        <h4 style='margin-bottom: 8px;'>{away} @ {home} <span style='font-weight:normal;'>🕒 {game_time_et}</span></h4>
        <p style='margin:4px 0;'><strong>Top1:</strong> {highlight(away_leadoff)} vs. {home_pitcher}</p>
        <p style='margin:4px 0;'><strong>Bot1:</strong> {highlight(home_leadoff)} vs. {away_pitcher}</p>
    </div>
    """, unsafe_allow_html=True)
