import pandas as pd

def calculate_last_5_game_stats(log_file="mlb_fp_logs.csv", output_file="last_5_fp_stats.csv"):
    df = pd.read_csv(log_file, parse_dates=["Date"])
    df = df.sort_values(["Player", "Date"], ascending=[True, False])

    players = []
    for player, group in df.groupby("Player"):
        last5 = group.head(5)

        swings = last5["First_Pitch_Swing"].sum()
        inplay = last5["First_Pitch_InPlay"].sum()
        xbh = last5["XBH"].sum()
        xba = last5["xBA"].mean()
        hand = last5["BatterHand"].iloc[0]
        games = len(last5)

        total_pitches = games  # since it's first pitch only, each row is 1 PA

        if total_pitches > 0:
            swing_pct = round((swings / total_pitches) * 100, 1)
            inplay_pct = round((inplay / total_pitches) * 100, 1)
            xbh_pct = round((xbh / total_pitches) * 100, 1)
        else:
            swing_pct = inplay_pct = xbh_pct = 0.0

        players.append({
            "Player": player,
            "GamesCounted": games,
            "First_Pitch_Swings": swings,
            "First_Pitch_InPlay": inplay,
            "First_Pitch_XBH": xbh,
            "xBA": round(xba, 3),
            "Swing%": swing_pct,
            "InPlay%": inplay_pct,
            "XBH%": xbh_pct,
            "BatterHand": hand
        })

    result_df = pd.DataFrame(players)
    result_df.to_csv(output_file, index=False)
    print(f"✅ Saved last-5-game first pitch stats to {output_file}")

if __name__ == "__main__":
    calculate_last_5_game_stats()
