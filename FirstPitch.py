import streamlit as st
from mlb_first_pitch import get_hot_hitters
import pandas as pd

st.set_page_config(page_title="FirstPitch Dashboard", layout="wide")
st.title("\u26be FirstPitch Dashboard")
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

    st.subheader("Top 5 Hot Hitters (Last 5 PAs with 3+ First Pitch Successes)")
    if not hot_hitters.empty:
        st.dataframe(
            hot_hitters.head(5)[["Batter", "First Pitch PAs", "In-Play/Hit Outcome"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hot hitters found with current criteria.")
else:
    st.info("Click 'Refresh Hot Hitters' to load data.")
