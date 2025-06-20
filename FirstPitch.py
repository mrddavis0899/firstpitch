import streamlit as st
import pandas as pd
import requests
import datetime
import json
import os

# --- Load Target List ---
TARGET_FILE = "target_hitters.json"

def load_targets():
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r") as f:
            return json.load(f)
    return []

def save_targets(target_list):
    with open(TARGET_FILE, "w") as f:
        json.dump(target_list, f)

# Load or initialize target list
if "target_hitters" not in st.session_state:
    st.session_state["target_hitters"] = load_targets()

# --- Page config ---
st.set_page_config(page_title="FirstPitch", layout="wide")

# --- Function to get today's live games ---
def get_live_game_ids():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=linescore"
    response = requests.get(url)
    data = response.json()
    game_ids = []
    for game in data["dates"][0]["games"]:
        if game["status"]["detailedState"] == "In Progress":
            game_ids.append({
                "gamePk": game["gamePk"],
                "home": game["teams"]["home"]["team"]["name"],
                "away": game["teams"]["away"]["team"]["name"]
            })
    return game_ids

# --- Get game feed for a specific game ---
def get_game_feed(gamePk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live"
    response = requests.get(url)
    return response.json()

# --- Determine next inning leadoff hitter ---
def get_leadoff_candidate(game_feed):
    try:
        inning = game_feed["liveData"]["linescore"]["currentInning"]
        half = game_feed["liveData"]["linescore"]["inningHalf"]
        outs = game_feed["liveData"]["linescore"]["outs"]

        offense = game_feed["liveData"]["linescore"]["offense"]
        offense_abbr = offense["abbreviation"]

        home_team = game_feed["gameData"]["teams"]["home"]["abbreviation"]
        away_team = game_feed["gameData"]["teams"]["away"]["abbreviation"]

        if offense_abbr == home_team:
            lineup = game_feed["liveData"]["boxscore"]["teams"]["home"].get("battingOrder", [])
            hitters = game_feed["liveData"]["boxscore"]["teams"]["home"]["players"]
        else:
            lineup = game_feed["liveData"]["boxscore"]["teams"]["away"].get("battingOrder", [])
            hitters = game_feed["liveData"]["boxscore"]["teams"]["away"]["players"]

        if not lineup or "battingOrder" not in game_feed["liveData"]["linescore"]:
            return None, None, None, None

        if outs == 3:
            current_index = game_feed["liveData"]["linescore"]["battingOrder"]
            if current_index in lineup:
                spot = lineup.index(current_index)
                next_spot = (spot + 1) % len(lineup)
                hitter_id = lineup[next_spot]
                hitter_key = f'ID{hitter_id}'
                hitter_name = hitters[hitter_key]["person"]["fullName"]
                next_half = "Top" if half == "Bottom" else "Bottom"
                return hitter_name, offense_abbr, inning + 1, next_half
        return None, None, None, None
    except Exception:
        return None, None, None, None

# --- Display Live Alerts ---
st.title("\u26be FirstPitch: Live Leadoff Tracker")
st.subheader("Real-time alerts when your favorite hitters are due to lead off.")

alert_rows = []
game_ids = get_live_game_ids()

for game in game_ids:
    gamePk = game["gamePk"]
    game_feed = get_game_feed(gamePk)
    matchup = f"{game['away']} @ {game['home']}"

    hitter, team, next_inning, half = get_leadoff_candidate(game_feed)

    if hitter:
        is_target = "\u2705" if hitter in st.session_state["target_hitters"] else "\u2014"
        alert_rows.append({
            "Matchup": matchup,
            "Next Inning": f"{half} {next_inning}",
            "Leadoff Hitter": hitter,
            "Target?": is_target
        })

        if hitter in st.session_state["target_hitters"]:
            st.success(f"\U0001F514 {hitter} is leading off the {half} {next_inning} in {matchup}!")

if alert_rows:
    st.header("\U0001F4E1 Upcoming Leadoff Hitters")
    st.table(pd.DataFrame(alert_rows))
else:
    st.info("No target hitters leading off the next inning yet.")
