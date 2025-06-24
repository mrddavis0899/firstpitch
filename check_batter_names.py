import pandas as pd

# Load your main batter dataset
df = pd.read_csv("first_pitch_data_2025.csv")

# Top 20 most frequent batters
print("\n🔝 Top 20 Batters by First Pitches Seen:")
print(df["batter_name"].value_counts().head(20))

# Unique batter count
print("\n👥 Total Unique Batters:")
print(df["batter_name"].nunique())

# Check for any pitcher names showing up as batters
suspect_pitchers = ["Spencer Schwellenbach", "Tucker Barnhart", "Nick Martinez"]
print("\n⚠️ Suspect Pitchers Appearing as Batters:")
print(df[df["batter_name"].isin(suspect_pitchers)])
