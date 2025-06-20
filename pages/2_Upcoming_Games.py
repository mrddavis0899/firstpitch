import streamlit as st
import pandas as pd
import requests
import datetime
import pytz

st.title("📅 Upcoming MLB Games")
st.subheader("All games scheduled today, with inning and start time in EST")

def get_today_games():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}&hydrate=team,linescore"
    response = requests.get(url)
    data = response.json()
    eastern = pytz.timezone("US/Eastern")
    
    games = []
    for game in data["dates"][0]["games"]:
        home = game["teams"]["home"]["team"]["name"]
        away = game["teams"]["away"]["team"]["name"]
        linescore = game.get("linescore", {})
        inning = linescore.get("currentInning", "-")
        half = linescore.get("inningHalf", "")
        inning_display = f"{half} {inning}" if inning != "-" else "Not Started"

        # Convert start time
        game_time_utc = datetime.datetime.fromisoformat(game["gameDate"].replace("Z", "+00:00"))
        game_time_est = game_time_utc.astimezone(eastern)
        start_time = game_time_est.strftime("%I:%M %p")

        games.append({
            "Matchup": f"{away} @ {home}",
            "Inning": inning_display,
            "Start Time (EST)": start_time
        })

    return games

games = get_today_games()

if games:
    st.table(pd.DataFrame(games))
else:
    st.info("No games found for today.")
