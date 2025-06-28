import pandas as pd
import os

# Load the full 2025 raw data file
RAW_FILE = "first_pitch_data_2025.csv"
CLEANED_FILE = "first_pitch_data_2025_cleaned.csv"

if not os.path.exists(RAW_FILE):
    raise FileNotFoundError(f"{RAW_FILE} not found. Make sure the raw file exists.")

# Load CSV
df = pd.read_csv(RAW_FILE)

# Ensure essential columns exist
required_cols = {"pitcher", "player_name", "events", "description", "stand", "p_throws", "game_date"}
if not required_cols.issubset(df.columns):
    raise ValueError("Missing expected columns in the raw dataset.")

# Clean up: remove null pitchers, drop unnecessary columns if needed
pitcher_df = df.dropna(subset=["pitcher", "player_name"])
pitcher_df = pitcher_df[pitcher_df["pitcher"].notnull()]

# Optionally remove duplicate pitcher appearances on first pitches
pitcher_df = pitcher_df.drop_duplicates(subset=["pitcher", "game_date"])

# Save cleaned file
pitcher_df.to_csv(CLEANED_FILE, index=False)
print(f"✅ Saved cleaned pitcher data to {CLEANED_FILE}")
