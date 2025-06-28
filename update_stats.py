
import pandas as pd
from pybaseball import statcast
from datetime import datetime

def fetch_and_process_statcast(start, end):
    print("⏳ Fetching Statcast data (MLB only)...")
    df = statcast(start_dt=start, end_dt=end)
    print(f"✅ Pulled {len(df)} rows of data.")

    # Only include 1st pitch of each at-bat
    df_fp = df[df["pitch_number"] == 1].copy()

    # Only include real hitters (exclude pitchers)
    df_fp = df_fp[df_fp["stand"].isin(["R", "L"])]
    df_fp = df_fp[df_fp["events"].notna()]

    # Clean up missing values
    df_fp["events"] = df_fp["events"].fillna("")

    # Add result columns
    df_fp["First_Pitch_Swing"] = df_fp["description"].isin(["swinging_strike", "foul", "hit_into_play"])
    df_fp["First_Pitch_InPlay"] = df_fp["description"] == "hit_into_play"
    df_fp["Single"] = df_fp["events"] == "single"
    df_fp["Double"] = df_fp["events"] == "double"
    df_fp["HomeRun"] = df_fp["events"] == "home_run"
    df_fp["XBH"] = df_fp["Double"] | df_fp["HomeRun"]

    # Infer team using inning_topbot
    df_fp["Team"] = df_fp.apply(
        lambda row: row["away_team"] if row["inning_topbot"] == "Top" else row["home_team"],
        axis=1
    )

    # Save most recent team for each player
    df_fp["game_date"] = pd.to_datetime(df_fp["game_date"])
    latest_teams = df_fp.sort_values("game_date").groupby("player_name")["Team"].last()

    # Group stats by player
    summary = df_fp.groupby("player_name").agg(
        Total_First_Pitches=("pitch_type", "count"),
        First_Pitch_Swings=("First_Pitch_Swing", "sum"),
        First_Pitch_InPlay=("First_Pitch_InPlay", "sum"),
        First_Pitch_XBH=("XBH", "sum"),
        xBA=("estimated_ba_using_speedangle", "mean"),
        BatterHand=("stand", lambda x: x.mode()[0] if not x.mode().empty else "R"),
        Singles=("Single", "sum"),
        Doubles=("Double", "sum"),
        HR=("HomeRun", "sum"),
    ).reset_index()

    # Exclude likely pitchers and fringe hitters
    summary = summary[summary["Total_First_Pitches"] >= 10]

    # Attach team info
    summary["Team"] = summary["player_name"].map(latest_teams)

    # Calculate percentages
    summary["Swing%"] = (summary["First_Pitch_Swings"] / summary["Total_First_Pitches"] * 100).round(1)
    summary["InPlay%"] = (summary["First_Pitch_InPlay"] / summary["Total_First_Pitches"] * 100).round(1)
    summary["XBH%"] = (summary["First_Pitch_XBH"] / summary["Total_First_Pitches"] * 100).round(1)
    summary["xBA"] = summary["xBA"].round(3)

    # Rename for UI
    summary.rename(columns={
        "player_name": "Player",
        "Singles": "1B",
        "Doubles": "2B",
        "HR": "HR"
    }, inplace=True)

    # Save raw first pitch data for Hot Hitters
    df_fp.to_csv("first_pitch_data_2025.csv", index=False)
    print("✅ Saved full first-pitch PAs to first_pitch_data_2025.csv")

    return summary

def main():
    start = "2025-03-20"
    end = datetime.today().strftime("%Y-%m-%d")
    summary_df = fetch_and_process_statcast(start, end)
    summary_df.to_csv("mlb_fp_stats.csv", index=False)
    print("✅ Saved hitter-first-pitch stats to mlb_fp_stats.csv")

if __name__ == "__main__":
    main()
