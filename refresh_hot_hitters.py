import pandas as pd
from datetime import datetime, timedelta
import os
from unidecode import unidecode

# Load raw data
df = pd.read_csv("first_pitch_hitters_2025.csv")

# Filter to last 14 days + first pitches only
df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
df = df[df["game_date"] >= datetime.now() - timedelta(days=14)]
df = df[df["pitch_number"] == 1]

# Success criteria
success_events = ["single", "double", "triple", "home_run"]
success_descriptions = [
    "hit_into_play", "field_out", "force_out", "grounded_into_double_play", "sac_fly"
]

df["success_no_ball"] = df["description"].isin(success_descriptions) | df["events"].isin(success_events)
df["success_with_ball"] = df["success_no_ball"] | (df["description"] == "ball")

# Get last 10 first-pitch PAs per batter
df = df.sort_values("game_date", ascending=False)
grouped = df.groupby("batter").head(10)

# Summarize
summary = grouped.groupby("batter").agg(
    total_pa=("description", "count"),
    success_with_ball=("success_with_ball", "sum"),
    success_no_ball=("success_no_ball", "sum")
).reset_index()

# Load name lookup
try:
    lookup = pd.read_csv("player_name_lookup.csv")
    id_to_name = dict(zip(lookup["key_mlbam"], lookup["full_name"]))
    summary["Batter"] = summary["batter"].map(id_to_name)
except:
    summary["Batter"] = summary["batter"]

# Save filtered versions
os.makedirs("data", exist_ok=True)

# With ball
with_ball = summary[(summary["total_pa"] >= 5) & (summary["success_with_ball"] >= 3)].copy()
with_ball["Successes"] = with_ball["success_with_ball"]
with_ball[["Batter", "total_pa", "Successes"]].rename(columns={"total_pa": "First Pitch PAs"}).to_csv(
    "data/hot_hitters_with_ball.csv", index=False)

# No ball
no_ball = summary[(summary["total_pa"] >= 5) & (summary["success_no_ball"] >= 3)].copy()
no_ball["Successes"] = no_ball["success_no_ball"]
no_ball[["Batter", "total_pa", "Successes"]].rename(columns={"total_pa": "First Pitch PAs"}).to_csv(
    "data/hot_hitters_no_ball.csv", index=False)

print("✅ Done. Both hot hitter files regenerated.")
