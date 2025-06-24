# pages/1_Target_Hitters.py
import streamlit as st
import json
import os
import requests
from unidecode import unidecode
from datetime import datetime
import pytz
import pandas as pd

st.title("🎯 Manage Target Hitters")

# --- Normalize Helper ---
def normalize(name):
    return unidecode(name).lower().strip()

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

# --- Initialize Session State ---
if "target_hitters" not in st.session_state:
    st.session_state["target_hitters"] = load_targets()

# --- Get Live Hitter Names ---
def get_live_hitters():
    hitters = set()
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    target_date = (now - pd.Timedelta(days=1)).strftime("%Y-%m-%d") if now.hour < 4 else now.strftime("%Y-%m-%d")
    schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}&hydrate=team,linescore"
    r = requests.get(schedule_url)
    data = r.json()
    games = data.get("dates", [{}])[0].get("games", [])

    for game in games:
        if game.get("status", {}).get("detailedState") != "In Progress":
            continue
        for side in ["home", "away"]:
            try:
                boxscore_url = f"https://statsapi.mlb.com/api/v1/game/{game['gamePk']}/boxscore"
                boxscore = requests.get(boxscore_url).json()
                team_players = boxscore["teams"][side]["players"]
                batters = boxscore["teams"][side]["batters"]
                for pid in batters:
                    pdata = team_players.get(f"ID{pid}", {})
                    pos_code = pdata.get("person", {}).get("primaryPosition", {}).get("code", "")
                    if pos_code != "P":
                        name = pdata.get("person", {}).get("fullName", "")
                        hitters.add(name)
            except:
                continue
    return sorted(hitters)

# --- Dropdown to Select from Live Hitters ---
live_hitters = get_live_hitters()
if live_hitters:
    st.subheader("📡 Add from Live Games")
    selected = st.multiselect("Choose hitters from current live lineups:", live_hitters)
    for name in selected:
        if name not in st.session_state["target_hitters"]:
            st.session_state["target_hitters"].append(name)
    if selected:
        save_targets(st.session_state["target_hitters"])
        st.success("Selected hitters added.")

# --- Manual Add Option ---
st.subheader("📝 Manually Add Target")
new_target = st.text_input("Type a new target hitter:")
if st.button("Add Hitter") and new_target:
    if new_target not in st.session_state["target_hitters"]:
        st.session_state["target_hitters"].append(new_target)
        save_targets(st.session_state["target_hitters"])
        st.success(f"{new_target} added to your list.")
    else:
        st.warning(f"{new_target} is already in your list.")

# --- Show Current List ---
st.subheader("Current Target Hitters")
if st.session_state["target_hitters"]:
    for hitter in st.session_state["target_hitters"]:
        st.markdown(f"- {hitter}")
else:
    st.info("You have no target hitters saved.")

# --- Remove Target ---
remove_target = st.selectbox("Remove a hitter:", options=["Select..."] + st.session_state["target_hitters"])
if st.button("Remove Selected Hitter") and remove_target != "Select...":
    st.session_state["target_hitters"].remove(remove_target)
    save_targets(st.session_state["target_hitters"])
    st.success(f"{remove_target} removed from your list.")
