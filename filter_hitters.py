import pandas as pd

# Load original Statcast data
df = pd.read_csv("first_pitch_data_2025.csv")

# Ensure the batter column exists
if "batter" not in df.columns or "player_name" not in df.columns:
    raise KeyError("Expected 'batter' or 'player_name' column missing in CSV.")

# Rename 'batter' to 'batter_id' and convert to numeric
df["batter_id"] = pd.to_numeric(df["batter"], errors="coerce")

# Normalize player name for consistency
df["player_name"] = df["player_name"].astype(str).str.strip().str.lower()

# Save cleaned file back to same name
df.to_csv("first_pitch_data_2025.csv", index=False)
print("✅ Saved: first_pitch_data_2025.csv with 'batter_id' and lowercase names.")
