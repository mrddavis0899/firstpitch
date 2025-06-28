# save as: generate_player_lookup.py
import pandas as pd
from pybaseball import playerid_reverse_lookup

# You can pull from your actual dataset
df = pd.read_csv("first_pitch_data_2025.csv")
unique_ids = df["batter"].dropna().unique().astype(int)

# Use pybaseball to reverse lookup IDs
lookup_df = playerid_reverse_lookup(unique_ids, key_type='mlbam')

# Clean and save
lookup_df["full_name"] = (lookup_df["name_first"] + " " + lookup_df["name_last"]).str.lower()
lookup_df[["key_mlbam", "full_name"]].to_csv("player_name_lookup.csv", index=False)

print("✅ Saved player_name_lookup.csv")
