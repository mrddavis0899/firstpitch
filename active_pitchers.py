# active_pitchers.py

from pybaseball import statcast, playerid_reverse_lookup
from datetime import date
import pandas as pd

print("📊 Loading 2025 Statcast data (this may take a minute)...")
start = "2025-03-20"
end = date.today().strftime("%Y-%m-%d")
df = statcast(start, end)

# Only keep rows where a pitch was thrown (to get pitchers)
df = df[df["pitch_number"].notna()]
pitcher_ids = df["pitcher"].dropna().unique()

print(f"👥 Found {len(pitcher_ids)} unique pitcher IDs")

# Lookup names for those pitchers
print("🔍 Looking up pitcher names...")
id_map = playerid_reverse_lookup(pitcher_ids, key_type='mlbam')
id_map["name"] = (id_map["name_first"] + " " + id_map["name_last"]).str.lower().str.strip()

# Save to CSV
pitcher_names = id_map[["key_mlbam", "name"]].drop_duplicates()
pitcher_names.to_csv("active_pitchers_2025.csv", index=False)
print("✅ Saved to active_pitchers_2025.csv")
