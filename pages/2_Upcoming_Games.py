import streamlit as st
import pandas as pd
import statsapi
from datetime import datetime

st.title("Upcoming Games")

# Fetch today's games
today = datetime.now().strftime("%Y-%m-%d")
games = statsapi.schedule(date=today)

if not games:
    st.warning("No MLB games found for today.")
else:
    game_rows = []
    for game in games:
        home_team = game.get('home_name', 'TBD')
        away_team = game.get('away_name', 'TBD')
        home_pitcher = game.get('home_probable_pitcher', {}).get('fullName', 'TBD') if isinstance(game.get('home_probable_pitcher'), dict) else 'TBD'
        away_pitcher = game.get('away_probable_pitcher', {}).get('fullName', 'TBD') if isinstance(game.get('away_probable_pitcher'), dict) else 'TBD'
        game_time = game.get('game_datetime', 'TBD')
        game_rows.append({
            "Home": home_team,
            "Away": away_team,
            "Home Pitcher": home_pitcher,
            "Away Pitcher": away_pitcher,
            "Time": game_time
        })

    st.subheader(f"Today's Games ({today})")
    df = pd.DataFrame(game_rows)
    st.dataframe(df, use_container_width=True)
