import streamlit as st
import statsapi
from datetime import datetime
import pytz
import json
import os

st.title("🗓️ Upcoming Games")

# Refresh button
if st.sidebar.button("🔄 Refresh Lineups"):
    st.rerun()

# Display last check time
now_est = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %I:%M:%S %p EST")
st.markdown(f"⏰ **Lineups last checked:** {now_est}")

def convert_to_est(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Eastern"))
        return dt.strftime("%-I:%M %p EST")
    except:
        return "TBD"

# Ensure /data folder exists
os.makedirs("data", exist_ok=True)
projected_pitchers_today = set()
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

            # Track pitchers
            if ap and ap != "TBD":
                projected_pitchers_today.add(ap)
            if hp and hp != "TBD":
                projected_pitchers_today.add(hp)

            # Load game data
            gid = game["game_id"]
            gd = statsapi.get("game", {"gamePk": gid})
            away_players = gd.get("away", {}).get("players", {})
            home_players = gd.get("home", {}).get("players", {})
            ao = gd.get("away", {}).get("battingOrder", [])
            ho = gd.get("home", {}).get("battingOrder", [])

            def extract_leadoff(order, players, is_home):
                if order:
                    return players.get(f"ID{order[0]}", {}).get("person", {}).get("fullName", "TBD")
                else:
                    # Try to find jersey numbers 1–9 (batting order placeholders)
                    for p in players.values():
                        if p.get("battingOrder", 9999) == 1:
                            name = p.get("person", {}).get("fullName", "TBD")
                            return f"⚠️ {name}"
                return "TBD"

            top1 = extract_leadoff(ao, away_players, False)
            bot1 = extract_leadoff(ho, home_players, True)

            def format_name(name):
                clean = name.replace("⚠️", "").strip()
                label = f"🎯 {name}" if clean.lower() in norm_targets else name
                if "⚠️" in name:
                    return f'<span style="color: goldenrod;">{label}</span>'
                return label

            label = f"{away} @ {home} – {stime}"
            with st.expander(label):
                st.markdown(f"**Top1:** {format_name(top1)} vs. {hp}", unsafe_allow_html=True)
                st.markdown(f"**Bot1:** {format_name(bot1)} vs. {ap}", unsafe_allow_html=True)

                if "TBD" in top1 or "TBD" in bot1:
                    st.info("🕒 Lineups not yet posted. Projections shown in yellow if available.")

        except Exception as e:
            st.error(f"Error processing {away} @ {home}: {e}")

    # Save pitcher list
    with open("data/projected_pitchers_today.json", "w") as f:
        json.dump(sorted(projected_pitchers_today), f, indent=2)
