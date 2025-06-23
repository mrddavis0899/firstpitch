import streamlit as st
import statsapi
from datetime import datetime
import pytz
import json
import os

st.title("🗓️ Upcoming Games")

def convert_to_est(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Eastern"))
        return dt.strftime("%-I:%M %p EST")
    except:
        return "TBD"

# Ensure data folder exists
os.makedirs("data", exist_ok=True)
projected_pitchers_today = set()

# Today's games
today = datetime.now().strftime("%Y-%m-%d")
games = statsapi.schedule(date=today)

if not games:
    st.warning("No MLB games today.")
else:
    target_hitters = st.session_state.get("target_hitters", set())
    norm_targets = {n.lower() for n in target_hitters}

    for game in games:
        try:
            away = game.get("away_name", "")
            home = game.get("home_name", "")
            ap = game.get("away_probable_pitcher", "")
            hp = game.get("home_probable_pitcher", "")
            ap = ap.get("fullName", ap) if isinstance(ap, dict) else ap
            hp = hp.get("fullName", hp) if isinstance(hp, dict) else hp
            stime = convert_to_est(game.get("game_datetime", ""))

            # Track pitchers for Trend Explorer
            if ap and ap != "TBD":
                projected_pitchers_today.add(ap)
            if hp and hp != "TBD":
                projected_pitchers_today.add(hp)

            # Default to "TBD" unless we successfully get leadoff names
            top1 = "TBD"
            bot1 = "TBD"

            # Try to pull leadoff hitters if batting orders exist
            gid = game["game_id"]
            gd = statsapi.get("game", {"gamePk": gid})
            ao = gd.get("away", {}).get("battingOrder", [])
            ho = gd.get("home", {}).get("battingOrder", [])
            apdict = gd.get("away", {}).get("players", {})
            hpdict = gd.get("home", {}).get("players", {})
            if ao:
                top1 = apdict.get(f"ID{ao[0]}", {}).get("person", {}).get("fullName", "TBD")
            if ho:
                bot1 = hpdict.get(f"ID{ho[0]}", {}).get("person", {}).get("fullName", "TBD")

            top1_lbl = "🎯 " + top1 if top1.lower() in norm_targets else top1
            bot1_lbl = "🎯 " + bot1 if bot1.lower() in norm_targets else bot1

            label = f"{away} @ {home} – {stime}"
            with st.expander(label):
                st.markdown(f"**Top1:** {top1_lbl} vs. {hp}")
                st.markdown(f"**Bot1:** {bot1_lbl} vs. {ap}")

                if top1 == "TBD" or bot1 == "TBD":
                    st.info("✅ Lineups will populate closer to game time. Check back ~1 hour before first pitch.")

        except Exception as e:
            st.error(f"Error processing {away} @ {home}: {e}")

    # Save projected pitchers to file
    with open("data/projected_pitchers_today.json", "w") as f:
        json.dump(sorted(projected_pitchers_today), f, indent=2)
