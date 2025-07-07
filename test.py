import pandas as pd

# Josh Naylor's MLBAM ID
naylor_id = 647304

# Load the raw Statcast first-pitch file
df = pd.read_csv("first_pitch_hitters_2025.csv")

# Filter for first-pitch only
df = df[df["pitch_number"] == 1]

# Filter for Josh Naylor
df = df[df["batter"] == naylor_id]

# Sort by actual PA order (latest PAs first)
df["game_date"] = pd.to_datetime(df["game_date"])
sort_cols = [col for col in ["game_date", "game_pk", "at_bat_number"] if col in df.columns]
df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))

# Show last 10 first-pitch PAs
recent = df.head(10)[["game_date", "inning", "at_bat_number", "description", "events"]]

print(recent)
