import pandas as pd
from datetime import datetime, timedelta
import os

def get_hot_hitters(include_ball=False):
    df = pd.read_csv("first_pitch_hitters_2025.csv")

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df[df["game_date"] >= datetime.now() - timedelta(days=14)]
    df = df[df["pitch_number"] == 1]

    success_events = ["single", "double", "triple", "home_run"]
    success_descriptions = [
        "hit_into_play", "field_out", "force_out", "grounded_into_double_play", "sac_fly"
    ]

    df["success_no_ball"] = df["description"].isin(success_descriptions) | df["events"].isin(success_events)
    df["success_with_ball"] = df["success_no_ball"] | (df["description"] == "ball")

    df = df.sort_values("game_date", ascending=False)
    grouped = df.groupby("batter").head(10)

    print("Unique batters before filter:", grouped['batter'].nunique())

    summary = grouped.groupby("batter").agg(
        total_pa=("description", "count"),
        success_with_ball=("success_with_ball", "sum"),
        success_no_ball=("success_no_ball", "sum")
    ).reset_index()

    if include_ball:
        summary = summary[(summary["total_pa"] == 10) & (summary["success_with_ball"] >= 8)]
        summary["Successes"] = summary["success_with_ball"]
        save_path = "data/hot_hitters_with_ball.csv"
    else:
        summary = summary[(summary["total_pa"] == 10) & (summary["success_no_ball"] >= 4)]
        summary["Successes"] = summary["success_no_ball"]
        save_path = "data/hot_hitters_no_ball.csv"

    print("Included after filter:", summary.shape[0])
    print(summary[["batter", "total_pa", "Successes"]].head(10))

    try:
        lookup = pd.read_csv("player_name_lookup.csv")
        id_to_name = dict(zip(lookup["key_mlbam"], lookup["full_name"]))
        summary["Batter"] = summary["batter"].map(id_to_name)
    except:
        summary["Batter"] = summary["batter"]

    summary["Batter"] = summary["Batter"].astype(str).str.lower().str.strip()

    final_df = summary[["Batter", "total_pa", "Successes"]].rename(columns={"total_pa": "First Pitch PAs"})
    final_df = final_df.sort_values("Successes", ascending=False)

    os.makedirs("data", exist_ok=True)
    final_df.to_csv(save_path, index=False)

    return final_df

# Run both versions
get_hot_hitters(include_ball=True)
get_hot_hitters(include_ball=False)
