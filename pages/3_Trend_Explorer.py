import streamlit as st
import pandas as pd
import os
from datetime import date
from pybaseball import statcast, playerid_reverse_lookup

CSV_FILE = "first_pitch_data_2025.csv"

@st.cache_data

def load_first_pitch_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)

    # Pull full 2025 season data
    start = "2025-03-20"
    end = date.today().strftime("%Y-%m-%d")
    df = statcast(start, end)

    # First pitch only
    df = df[df["pitch_number"] == 1].copy()

    # Add batter name from ID
    batter_ids = df["batter"].dropna().unique()
    id_map = playerid_reverse_lookup(batter_ids)
    id_map = id_map[["key_mlbam", "name_first", "name_last"]]
    id_map["batter_name"] = id_map["name_first"] + " " + id_map["name_last"]
    df = df.merge(id_map[["key_mlbam", "batter_name"]], left_on="batter", right_on="key_mlbam", how="left")

    df.to_csv(CSV_FILE, index=False)
    return df

st.title("📊 Trend Explorer – First Pitch Performance")

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    st.cache_data.clear()
    st.rerun()

with st.spinner("Loading 2025 first pitch data..."):
    df = load_first_pitch_data()

# Group by batter and calculate stats
grouped = df.groupby("batter_name").agg(
    total_fp=("pitch_type", "count"),
    balls=("description", lambda x: (x == "ball").sum()),
    singles=("events", lambda x: (x == "single").sum()),
    xbh=("events", lambda x: x.isin(["double", "triple", "home_run"]).sum()),
    hits=("events", lambda x: x.isin(["single", "double", "triple", "home_run"]).sum()),
    fouls=("description", lambda x: (x == "foul").sum()),
    in_play=("description", lambda x: (x == "hit_into_play").sum()),
    swings=("description", lambda x: x.isin(["foul", "swinging_strike", "swinging_strike_blocked", "hit_into_play"]).sum()),
)

grouped["in_play_pct"] = (grouped["in_play"] / grouped["total_fp"]).round(3)
grouped["swing_pct"] = (grouped["swings"] / grouped["total_fp"]).round(3)
grouped = grouped.reset_index()

st.subheader("Search and Filter First Pitch Hitters")

min_fp = st.sidebar.slider("Minimum First Pitch ABs", 5, 100, 10)
filtered = grouped[grouped["total_fp"] >= min_fp]

# 🔍 Add batter name search above table
search_query = st.text_input("Search by batter name:")
if search_query:
    filtered = filtered[filtered["batter_name"].str.contains(search_query, case=False)]

# Show sortable table using st.dataframe
st.dataframe(
    filtered.sort_values("in_play_pct", ascending=False),
    use_container_width=True,
    hide_index=True
)

# Show total saved targets if any
target_list = st.session_state.get("target_hitters", set())
st.success(f"✅ {len(target_list)} hitters currently on your target list.")
