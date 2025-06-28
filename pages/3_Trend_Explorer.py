import streamlit as st
import pandas as pd
import os
import json
from datetime import date
from pybaseball import statcast, playerid_reverse_lookup

CSV_FILE = "first_pitch_hitters_2025.csv"
CLEANED_PITCHER_FILE = "first_pitch_data_2025_cleaned.csv"

@st.cache_data
def load_first_pitch_data():
    from pybaseball import statcast, playerid_reverse_lookup
    from datetime import date

    start = "2025-03-20"
    end = date.today().strftime("%Y-%m-%d")

    st.info("Fetching first pitch data...")

    # Pull Statcast data
    df = statcast(start, end)
    df = df[df["pitch_number"] == 1].copy()

    # Save full unfiltered first pitch data
    df.to_csv("first_pitch_data_2025.csv", index=False)

    # Remove likely pitchers from batter dataset
    batter_df = df[~df["player_name"].str.contains(" P$", na=False)]

    # Save hitters-only file
    batter_df.to_csv("first_pitch_hitters_2025.csv", index=False)

    return batter_df

    st.warning("⚠️ Data not found. Please click 'Refresh Batters Data' to generate stats.")
    return pd.DataFrame()

st.title("📊 Trend Explorer – First Pitch Performance")

if st.sidebar.button("🔄 Refresh Pitcher Data"):
    st.info("Refreshing pitcher data, please wait...")
    pitcher_data = statcast("2025-03-27", date.today().strftime("%Y-%m-%d"))
    pitcher_data = pitcher_data[pitcher_data["pitch_number"] == 1]

    pitcher_grouped = pitcher_data.groupby("pitcher").agg(
        **{
            "First Pitch Total": ("pitch_type", "count"),
            "First Pitch In-Play #": ("description", lambda x: (x == "hit_into_play").sum()),
            "First Pitch Ball #": ("description", lambda x: (x == "ball").sum()),
            "First Pitch Called Strike #": ("description", lambda x: (x == "called_strike").sum()),
            "First Pitch Swinging Strike #": ("description", lambda x: (x == "swinging_strike").sum()),
            "First Pitch Foul #": ("description", lambda x: (x == "foul").sum()),
            "First Pitch Hit #": ("events", lambda x: x.isin(["single", "double", "triple", "home_run"]).sum()),
            "First Pitch xBA": ("estimated_ba_using_speedangle", lambda x: x.mean(skipna=True)),
        }
    )

    pitcher_grouped["First Pitch In-Play %"] = (
        pitcher_grouped["First Pitch In-Play #"] / pitcher_grouped["First Pitch Total"]
    ).round(3)
    pitcher_grouped["First Pitch Ball %"] = (
        pitcher_grouped["First Pitch Ball #"] / pitcher_grouped["First Pitch Total"]
    ).round(3)
    pitcher_grouped["First Pitch Strike %"] = (
        (
            pitcher_grouped["First Pitch Called Strike #"] +
            pitcher_grouped["First Pitch Swinging Strike #"] +
            pitcher_grouped["First Pitch Foul #"]
        ) / pitcher_grouped["First Pitch Total"]
    ).round(3)
    pitcher_grouped["First Pitch xBA"] = pitcher_grouped["First Pitch xBA"].round(3)

    pitcher_grouped = pitcher_grouped.reset_index().rename(columns={"pitcher": "player_id"})
    name_map = playerid_reverse_lookup(pitcher_grouped["player_id"].tolist())
    name_map["player_name"] = name_map["name_first"] + " " + name_map["name_last"]
    merged = pitcher_grouped.merge(name_map[["key_mlbam", "player_name"]], left_on="player_id", right_on="key_mlbam", how="left")
    merged.to_csv(CLEANED_PITCHER_FILE, index=False)

    st.success("Pitcher data refreshed!")
    st.rerun()

if st.sidebar.button("🔄 Refresh Batter Data"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    st.cache_data.clear()
    st.rerun()
if st.sidebar.button("🧼 One-Click Full Refresh and Regenerate"):
    files = [
        "first_pitch_data_2025.csv",
        "first_pitch_hitters_2025.csv"
    ]
    for file in files:
        if os.path.exists(file):
            os.remove(file)

    st.cache_data.clear()
    st.info("Generating fresh first pitch data... please wait.")

    # Regenerate CSV
    df = load_first_pitch_data()

    if df.empty:
        st.error("❌ Failed to generate fresh data.")
    else:
        st.success("✅ First pitch data successfully refreshed and reloaded.")
        st.rerun()

with st.spinner("Loading 2025 first pitch data..."):
    df = load_first_pitch_data()

if df.empty:
    st.stop()

st.subheader("Search and Filter First Pitch Hitters")

df["batter"] = pd.to_numeric(df["batter"], errors="coerce")

lookup_df = pd.read_csv("player_name_lookup.csv")
id_to_name = dict(zip(lookup_df["key_mlbam"], lookup_df["full_name"]))

df["batter_name"] = df["batter"].map(id_to_name).str.lower()

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

st.markdown("---")
show_pitchers = st.toggle("🎯 Show Pitcher First Pitch Trends", value=True)

if show_pitchers:
    st.subheader("🎯 Pitcher First Pitch Trends")

    try:
        pitcher_df = pd.read_csv(CLEANED_PITCHER_FILE)
        pitcher_df = pitcher_df.rename(columns={"player_name": "pitcher_name"})
    except FileNotFoundError:
        st.warning("Missing cleaned pitcher data file. Please ensure first_pitch_data_2025_cleaned.csv exists.")
        st.stop()

    projected_path = "data/projected_pitchers_today.json"
    if os.path.exists(projected_path):
        with open(projected_path) as f:
            target_pitchers = set(json.load(f))
            norm_proj = set(p.lower() for p in target_pitchers)
    else:
        norm_proj = set()

    def normalize_name(name):
        if not isinstance(name, str):
            return ""
        if "," in name:
            parts = [p.strip().lower() for p in name.split(",")]
            return f"{parts[1]} {parts[0]}"
        return name.lower()

    pitcher_df["normalized_name"] = pitcher_df["pitcher_name"].apply(normalize_name)
    pitcher_df["pitcher_name"] = pitcher_df.apply(
        lambda row: "🌟 " + row["pitcher_name"] if row["normalized_name"] in norm_proj else row["pitcher_name"],
        axis=1
    )
    pitcher_df["Is Starred"] = pitcher_df["pitcher_name"].astype(str).str.startswith("🌟")
    pitcher_df["Is Starred"] = pitcher_df["Is Starred"].fillna(False)

    min_pitch_fp = st.sidebar.slider("Minimum First Pitch PAs (Pitchers)", 5, 100, 10)

    if "First Pitch Total" in pitcher_df.columns:
        pitcher_filtered = pitcher_df[pitcher_df["First Pitch Total"] >= min_pitch_fp]

        filter_starred = st.sidebar.checkbox("⭐ Show Only Starred Pitchers", value=False)
        if filter_starred:
            pitcher_filtered = pitcher_filtered[pitcher_filtered["Is Starred"]]

        pitcher_query = st.text_input("Search by pitcher name:")
        if pitcher_query:
            pitcher_filtered = pitcher_filtered[pitcher_filtered["pitcher_name"].str.contains(pitcher_query, case=False)]

        st.dataframe(
            pitcher_filtered.sort_values("First Pitch In-Play %", ascending=False)[[
                "pitcher_name",
                "First Pitch Total",
                "First Pitch In-Play #",
                "First Pitch In-Play %",
                "First Pitch Strike %",
                "First Pitch Ball %",
                "First Pitch Hit #",
                "First Pitch xBA"
            ]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("🚫 'First Pitch Total' column not found in pitcher data.")
        st.stop()