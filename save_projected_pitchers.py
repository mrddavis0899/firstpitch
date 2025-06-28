import json
import os
from datetime import datetime
from pytz import timezone
import statsapi

# Get today's date in Eastern Time
today = datetime.now(timezone("US/Eastern")).date()
print("Today (Eastern):", today)

# Get today's schedule
schedule = statsapi.schedule(date=today.strftime("%m/%d/%Y"))
print("Games found:", len(schedule))

projected_pitchers = set()

for game in schedule:
    print("Game:", game["away_name"], "@", game["home_name"])

    try:
        game_id = game["game_id"]
        full_game_data = statsapi.get("game", {"gamePk": game_id})

        # Extract pitchers
        away_pitcher = full_game_data.get("teams", {}).get("away", {}).get("probablePitcher", {}).get("fullName")
        home_pitcher = full_game_data.get("teams", {}).get("home", {}).get("probablePitcher", {}).get("fullName")

        print("  Away Probable:", away_pitcher or "N/A")
        print("  Home Probable:", home_pitcher or "N/A")

        if away_pitcher:
            projected_pitchers.add(away_pitcher)
        if home_pitcher:
            projected_pitchers.add(home_pitcher)

    except Exception as e:
        print("  ⚠️ Error fetching full game data:", e)

# Save to data/projected_pitchers_today.json
os.makedirs("data", exist_ok=True)
with open("data/projected_pitchers_today.json", "w") as f:
    json.dump(sorted(projected_pitchers), f)

print("✅ Saved projected pitchers:", len(projected_pitchers))
