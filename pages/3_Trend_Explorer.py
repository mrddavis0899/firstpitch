import streamlit as st
import pandas as pd
import os
import json
from datetime import date
from pybaseball import statcast, playerid_reverse_lookup

CSV_FILE = "first_pitch_data_2025.csv"

@st.cache_data
def load_first_pitch_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)

    start = "2025-03-20"
    end = date.today().strftime("%Y-%m-%d")
    df = statcast(start, end)
    df = df[df["pitch_number"] == 1].copy()

    # Add batter name
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

# === HITTER SECTION ===
st.subheader("Search and Filter First Pitch Hitters")

grouped = df.groupby("batter_name").agg(
    total_fp=("pitch_type", "count"),
    balls=("description", lambda x: (x == "ball").sum()),
    singles=("events", lambda x: (x == "single").sum()),
    xbh=("events", lambda x: x.isin(["double", "triple", "home_run"]).sum()),
    hits=("events", lambda x: x.isin(["single", "double", "triple", "home_run"]).sum()),
    fouls=("description", lambda x: (x == "foul").sum()),
    in_play=("description", lambda x: (x == "hit_into_play").sum()),
    swings=("description", lambda x: x.isin(["foul", "swinging_strike", "swinging_strike_blocked", "hit_into_play"]).sum()),
    strikes_looking=("description", lambda x: (x == "called_strike").sum())
)

# Add rates
grouped["in_play_pct"] = (grouped["in_play"] / grouped["total_fp"]).round(3)
grouped["swing_pct"] = (grouped["swings"] / grouped["total_fp"]).round(3)
grouped["strike_look_pct"] = (grouped["strikes_looking"] / grouped["total_fp"]).round(3)

grouped = grouped.reset_index()

min_fp = st.sidebar.slider("Minimum First Pitch ABs", 5, 100, 10)
filtered = grouped[grouped["total_fp"] >= min_fp]

search_query = st.text_input("Search by batter name:")
if search_query:
    filtered = filtered[filtered["batter_name"].str.contains(search_query, case=False)]

st.dataframe(
    filtered.sort_values("in_play_pct", ascending=False)[[
        "batter_name", "total_fp", "in_play", "in_play_pct",
        "swings", "swing_pct", "strikes_looking", "strike_look_pct",
        "xbh", "hits", "balls"
    ]],
    use_container_width=True,
    hide_index=True
)

# === PITCHER SECTION ===
st.markdown("---")
show_pitchers = st.toggle("🎯 Show Pitcher First Pitch Trends", value=True)

if show_pitchers:
    st.subheader("🎯 Pitcher First Pitch Trends")

    # Load projected starters
    projected_path = "data/projected_pitchers_today.json"
    if os.path.exists(projected_path):
        with open(projected_path) as f:
            target_pitchers = set(json.load(f))
            norm_proj = set(p.lower() for p in target_pitchers)
    else:
        norm_proj = set()

    def normalize_name(name):
        if "," in name:
            parts = [p.strip().lower() for p in name.split(",")]
            return f"{parts[1]} {parts[0]}"
        return name.lower()

    pitcher_stats = df.groupby("pitcher").agg(
        pitcher_name=("player_name", "first"),
        total_fp=("pitch_type", "count"),
        called_strikes=("description", lambda x: (x == "called_strike").sum()),
        swinging_strikes=("description", lambda x: (x == "swinging_strike").sum()),
        in_play=("description", lambda x: (x == "hit_into_play").sum()),
        balls=("description", lambda x: (x == "ball").sum()),
    ).reset_index()

    pitcher_stats["normalized_name"] = pitcher_stats["pitcher_name"].apply(normalize_name)
    pitcher_stats["pitcher_name"] = pitcher_stats.apply(
        lambda row: "🌟 " + row["pitcher_name"] if row["normalized_name"] in norm_proj else row["pitcher_name"], axis=1
    )

    pitcher_stats["fp_strike_pct"] = (
        (pitcher_stats["called_strikes"] + pitcher_stats["swinging_strikes"]) / pitcher_stats["total_fp"]
    ).round(3)
    pitcher_stats["fp_in_play_pct"] = (pitcher_stats["in_play"] / pitcher_stats["total_fp"]).round(3)
    pitcher_stats["fp_ball_pct"] = (pitcher_stats["balls"] / pitcher_stats["total_fp"]).round(3)

    min_pitch_fp = st.sidebar.slider("Minimum First Pitch PAs (Pitchers)", 5, 100, 10)
    pitcher_filtered = pitcher_stats[pitcher_stats["total_fp"] >= min_pitch_fp]

    pitcher_query = st.text_input("Search by pitcher name:")
    if pitcher_query:
        pitcher_filtered = pitcher_filtered[pitcher_filtered["pitcher_name"].str.contains(pitcher_query, case=False)]

    st.dataframe(
        pitcher_filtered.sort_values("fp_strike_pct", ascending=False)[[
            "pitcher_name", "total_fp", "fp_strike_pct", "fp_in_play_pct", "fp_ball_pct"
        ]],
        use_container_width=True,
        hide_index=True
    )
