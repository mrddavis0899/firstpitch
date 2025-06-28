import requests
from bs4 import BeautifulSoup
import json
import os

# URL of MLB probable pitchers page
url = "https://www.mlb.com/probable-pitchers"

# Get the page
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# New selector based on your screenshot
pitcher_tags = soup.find_all("a", class_="probable-pitchers__pitcher-name-link")

pitchers_today = set()

for tag in pitcher_tags:
    name = tag.get_text(strip=True)
    if name:
        pitchers_today.add(name.lower())  # Normalize

# Save to JSON
os.makedirs("data", exist_ok=True)
with open("data/projected_pitchers_today.json", "w") as f:
    json.dump(sorted(pitchers_today), f)

print(f"Saved {len(pitchers_today)} projected pitchers for today.")
