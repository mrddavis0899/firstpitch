import streamlit as st
from mlb_first_pitch import get_hot_hitters
import pandas as pd
import os
import datetime

st.set_page_config(page_title="FirstPitch Dashboard", layout="wide")
st.title("⚾ FirstPitch Dashboard")
st.markdown("Welcome to the FirstPitch Dashboard!")

st.markdown("---")

# Checkbox to include/exclude "ball" in success criteria
include_ball = st.checkbox("Include 'Ball' as a Successful First Pitch?", value=True)

# Refresh hot hitters
if st.button("Refresh Hot Hitters"):
    st.session_state.hot_hitters = get_hot_hitters(include_ball=include_ball)

# Display hot hitters if available
if "hot_hitters" in st.session_state:
    hot_hitters = st.session_state.hot_hitters

    st.subheader("Top 5 Hot Hitters (Last 10 First Pitch PAs with 5+ Successes)")
    if not hot_hitters.empty:
        st.dataframe(
            hot_hitters.head(5)[["Batter", "First Pitch PAs", "Successes"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hot hitters found with current criteria.")
else:
    st.info("Click 'Refresh Hot Hitters' to load data.")

# -------------------------
# 📦 STATS UPDATE SECTION
# -------------------------
st.markdown("---")
st.subheader("🔁 Data Maintenance")

# Show last modified time of first_pitch_data_2025.csv
csv_path = "first_pitch_data_2025.csv"
if os.path.exists(csv_path):
    mod_time = os.path.getmtime(csv_path)
    readable_time = datetime.datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"📅 Last data update: {readable_time}")
else:
    st.caption("⚠️ No data file found yet.")

# Button to run update_stats.py
if st.button("🔁 Update All Stats (Run update_stats.py)"):
    with st.spinner("Running update_stats.py..."):
        exit_code = os.system("python update_stats.py")
        if exit_code == 0:
            st.success("✅ All stats updated successfully. You can now refresh Hot Hitters.")
        else:
            st.error("❌ Failed to run update_stats.py. Make sure the file exists.")
