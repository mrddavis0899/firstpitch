import pandas as pd
import statsapi
from datetime import datetime, timedelta

def update_csvs():
    # Use tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"📅 Fetching games for {tomorrow}...")

    # Fetch schedule
    sched = statsapi.schedule(start_date=tomorrow, end_date=tomorrow, sportId=1)

    if not sched:
        print(f"⚠️ No games scheduled for {tomorrow}. games_today.csv not saved.")
        return

    # Build games data
    games = []
    for g in sched:
        games.append({
            'away_team': g['away_name'],
            'home_team': g['home_name'],
            'away_pitcher': '',  # You can populate these later if needed
            'home_pitcher': '',
            'StartTimeET': g['game_datetime']  # ISO timestamp
        })

    df = pd.DataFrame(games)
    df.to_csv("games_today.csv", index=False)
    print(f"✅ games_today.csv saved with {len(df)} games for {tomorrow}")
