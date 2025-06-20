# pages/1_Target_Hitters.py
import streamlit as st
import json
import os

st.title("🎯 Manage Target Hitters")

# --- Load Target List ---
TARGET_FILE = "target_hitters.json"

def load_targets():
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, "r") as f:
            return json.load(f)
    return []

def save_targets(target_list):
    with open(TARGET_FILE, "w") as f:
        json.dump(target_list, f)

# --- Initialize Session State ---
if "target_hitters" not in st.session_state:
    st.session_state["target_hitters"] = load_targets()

# --- Add New Target ---
new_target = st.text_input("Add a new target hitter:")
if st.button("Add Hitter") and new_target:
    if new_target not in st.session_state["target_hitters"]:
        st.session_state["target_hitters"].append(new_target)
        save_targets(st.session_state["target_hitters"])
        st.success(f"{new_target} added to your list.")
    else:
        st.warning(f"{new_target} is already in your list.")

# --- Show Current List ---
st.subheader("Current Target Hitters")
if st.session_state["target_hitters"]:
    for hitter in st.session_state["target_hitters"]:
        st.markdown(f"- {hitter}")
else:
    st.info("You have no target hitters saved.")

# --- Remove Target ---
remove_target = st.selectbox("Remove a hitter:", options=["Select..."] + st.session_state["target_hitters"])
if st.button("Remove Selected Hitter") and remove_target != "Select...":
    st.session_state["target_hitters"].remove(remove_target)
    save_targets(st.session_state["target_hitters"])
    st.success(f"{remove_target} removed from your list.")
