# pages/3_Trend_Explorer.py
import streamlit as st
import pandas as pd
from pybaseball import statcast, playerid_reverse_lookup
from datetime import date
import json
import os

st.title("📊 Trend Explorer: First Pitch Outcome Stats")
st.caption("Built from live 2025 Statcast data. Filter hitters by actual first pitch outcomes and save targets.")

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

# Initialize target list
if "target_hitters" not in st.session_state:
    st.session_state["target_hitters"] = load_targets()

# --- Load Statcast First Pitch Data ---
@st.cache_data(ttl=3600)
def load_first_pitch_data():
    start = "2025-03-20"
    end = date.today().strftime("%Y-%m-%d")
    df = statcast(start, end)
    df = df[df["pitch_number"] == 1]
    df = df.dropna(subset=["at_bat_number", "batter", "game_pk"])
    df = df.drop_duplicates(subset=["game_pk", "at_bat_number", "batter"])

    # Add batter_name from batter ID
    batter_ids = df["batter"].dropna().unique()
    id_map = playerid_reverse_lookup(batter_ids)
    id_map = id_map[["key_mlbam", "name_last", "name_first"]]
    id_map["batter_name"] = id_map["name_first"] + " " + id_map["name_last"]
    df = df.merge(id_map[["key_mlbam", "batter_name"]], left_on="batter", right_on="key_mlbam", how="left")

    return df

with st.spinner("Pulling 2025 Statcast data..."):
    df = load_first_pitch_data()

# --- Calculate Outcomes ---
grouped = df.groupby("batter_name").agg(
    total_fp=("pitch_type", "count"),
    balls=("description", lambda x: (x == "ball").sum()),
    singles=("events", lambda x: (x == "single").sum()),
    xb_hits=("events", lambda x: x.isin(["double", "triple", "home_run"]).sum())
)
grouped["others"] = grouped["total_fp"] - grouped["balls"] - grouped["singles"] - grouped["xb_hits"]

# Percentages
grouped["ball_pct"] = grouped["balls"] / grouped["total_fp"]
grouped["single_pct"] = grouped["singles"] / grouped["total_fp"]
grouped["xbh_pct"] = grouped["xb_hits"] / grouped["total_fp"]
grouped["other_pct"] = grouped["others"] / grouped["total_fp"]

# Filter
grouped = grouped[grouped["total_fp"] >= 25].round(3).reset_index()

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Hitters")
min_fp = st.sidebar.slider("Min First Pitch ABs", 10, 100, 25)
min_ball = st.sidebar.slider("Min Ball %", 0.0, 1.0, 0.0)
min_single = st.sidebar.slider("Min Single %", 0.0, 1.0, 0.0)
min_xbh = st.sidebar.slider("Min XBH %", 0.0, 1.0, 0.0)

filtered = grouped[
    (grouped["total_fp"] >= min_fp) &
    (grouped["ball_pct"] >= min_ball) &
    (grouped["single_pct"] >= min_single) &
    (grouped["xbh_pct"] >= min_xbh)
]

# --- Add Targets ---
st.subheader("📋 Eligible First Pitch Standouts")
selection = st.multiselect("Add hitters to your target list:", filtered["batter_name"].tolist())

for hitter in selection:
    if hitter not in st.session_state["target_hitters"]:
        st.session_state["target_hitters"].append(hitter)
        save_targets(st.session_state["target_hitters"])
        st.success(f"{hitter} added to your target list.")

# --- Show Table ---
st.dataframe(filtered[[
    "batter_name", "total_fp", "ball_pct", "single_pct", "xbh_pct", "other_pct"
]])

# --- Show Saved List ---
with st.expander("🎯 Current Target Hitters"):
    st.write(st.session_state["target_hitters"])
