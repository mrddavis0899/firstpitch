import pandas as pd
from datetime import datetime, timedelta

def get_hot_hitters(csv_path="first_pitch_data_2025.csv", pitcher_csv="active_pitchers_2025.csv", include_ball=True):
    df = pd.read_csv(csv_path)

    # Convert game_date to datetime and filter by last 7 days
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    last_week = datetime.now() - timedelta(days=7)
    df = df[df["game_date"] >= last_week]

    # Remove rows without batter name
    if "batter_name" not in df.columns:
        df["batter_name"] = df["player_name"]
    df = df[df["batter_name"].notna()]

    # Exclude pitchers
    try:
        pitchers = pd.read_csv(pitcher_csv)
        pitcher_names = pitchers["name"].str.lower().str.strip().unique()
        df = df[~df["batter_name"].str.lower().str.strip().isin(pitcher_names)]
    except Exception as e:
        print("⚠️ Pitcher filter skipped due to error:", e)

    # Sort by date and group by batter
    df_sorted = df.sort_values("game_date", ascending=False)
    grouped = df_sorted.groupby("batter_name")

    hot_hitters = []

    for batter, group in grouped:
        last_5 = group.head(5)
        pa_count = len(last_5)

        # Define success conditions
        if include_ball:
            success_mask = (
                last_5["description"].isin(["ball", "hit_into_play"]) |
                last_5["events"].isin(["single", "double", "triple", "home_run"])
            )
        else:
            success_mask = (
                last_5["description"].isin(["hit_into_play"]) |
                last_5["events"].isin(["single", "double", "triple", "home_run"])
            )

        successes = success_mask.sum()

        if pa_count >= 5 and successes >= 2:
            hot_hitters.append({
                "Batter": batter,
                "First Pitch PAs": pa_count,
                "In-Play/Hit Outcome": successes,
            })

    return pd.DataFrame(hot_hitters).sort_values(by="In-Play/Hit Outcome", ascending=False)
