import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st


HITTERS_CSV = "first_pitch_hitters_2025.csv"
LOOKUP_CSV = "player_name_lookup.csv"


def _get_download_url(file_name: str) -> str | None:
    """Get a direct-download URL from Streamlit secrets or environment variables."""
    try:
        if "csv_urls" in st.secrets and file_name in st.secrets["csv_urls"]:
            return st.secrets["csv_urls"][file_name]
    except Exception:
        pass

    env_map = {
        HITTERS_CSV: "FIRST_PITCH_HITTERS_URL",
        LOOKUP_CSV: "PLAYER_NAME_LOOKUP_URL",
    }
    env_key = env_map.get(file_name)
    return os.getenv(env_key) if env_key else None


@st.cache_data(show_spinner=False)
def load_csv(file_name: str) -> pd.DataFrame:
    """
    Load a CSV from local disk. If it is missing, try downloading it from a URL.
    Returns an empty DataFrame if the file still is not available.
    """
    if os.path.exists(file_name):
        return pd.read_csv(file_name)

    url = _get_download_url(file_name)
    if url:
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            with open(file_name, "wb") as f:
                f.write(response.content)
            return pd.read_csv(file_name)
        except Exception as e:
            print(f"Failed to download {file_name}: {e}")

    return pd.DataFrame()


def get_hot_hitters(include_ball: bool = False) -> pd.DataFrame:
    df = load_csv(HITTERS_CSV)

    empty_result = pd.DataFrame(columns=["Batter", "First Pitch PAs", "Successes"])
    save_path = "data/hot_hitters_with_ball.csv" if include_ball else "data/hot_hitters_no_ball.csv"

    if df.empty:
        os.makedirs("data", exist_ok=True)
        empty_result.to_csv(save_path, index=False)
        return empty_result

    required_cols = {"game_date", "pitch_number", "description", "events", "batter"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"Missing required columns in {HITTERS_CSV}: {sorted(missing)}")
        os.makedirs("data", exist_ok=True)
        empty_result.to_csv(save_path, index=False)
        return empty_result

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df[df["game_date"] >= datetime.now() - timedelta(days=14)]
    df = df[df["pitch_number"] == 1]

    success_events = ["single", "double", "triple", "home_run"]
    success_descriptions = [
        "hit_into_play",
        "field_out",
        "force_out",
        "grounded_into_double_play",
        "sac_fly",
    ]

    df["success_no_ball"] = df["description"].isin(success_descriptions) | df["events"].isin(success_events)
    df["success_with_ball"] = df["success_no_ball"] | (df["description"] == "ball")

    sort_cols = [col for col in ["game_date", "game_pk", "at_bat_number"] if col in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=[False] * len(sort_cols))

    grouped = df.groupby("batter").head(10)

    print("Unique batters before filter:", grouped["batter"].nunique())

    summary = grouped.groupby("batter").agg(
        total_pa=("description", "count"),
        success_with_ball=("success_with_ball", "sum"),
        success_no_ball=("success_no_ball", "sum"),
    ).reset_index()

    if include_ball:
        summary = summary[(summary["total_pa"] == 10) & (summary["success_with_ball"] >= 8)]
        summary["Successes"] = summary["success_with_ball"]
    else:
        summary = summary[(summary["total_pa"] == 10) & (summary["success_no_ball"] >= 4)]
        summary["Successes"] = summary["success_no_ball"]

    print("Included after filter:", summary.shape[0])
    if not summary.empty:
        print(summary[["batter", "total_pa", "Successes"]].head(10))

    lookup = load_csv(LOOKUP_CSV)
    if not lookup.empty and {"key_mlbam", "full_name"}.issubset(lookup.columns):
        id_to_name = dict(zip(lookup["key_mlbam"], lookup["full_name"]))
        summary["Batter"] = summary["batter"].map(id_to_name)
    else:
        summary["Batter"] = summary["batter"]

    summary["Batter"] = summary["Batter"].astype(str).str.lower().str.strip()

    final_df = summary[["Batter", "total_pa", "Successes"]].rename(columns={"total_pa": "First Pitch PAs"})
    final_df = final_df.sort_values("Successes", ascending=False)

    os.makedirs("data", exist_ok=True)
    final_df.to_csv(save_path, index=False)

    return final_df


if __name__ == "__main__":
    get_hot_hitters(include_ball=True)
    get_hot_hitters(include_ball=False)
