import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2 import service_account

# ---------- CONFIG ----------
SPREADSHEET_NAME = "Fanduel Bet Tracker"
STARTING_BANKROLL = 83.0

# ---------- GOOGLE SHEETS CONNECTION ----------
def connect_to_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(st.secrets["google"], scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet

def get_data(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def add_row(sheet, new_data):
    sheet.append_row(list(new_data.values()))

# ---------- UI ----------
st.title("📋 Bet Tracker")

sheet = connect_to_gsheet()

tab1, tab2 = st.tabs(["➕ Add Bet", "📊 View History"])

with tab1:
    st.subheader("Add a New Bet")

    date = st.date_input("Date", value=datetime.today())
    event = st.text_input("Event (e.g. Gators vs FSU)")
    bet_type = st.text_input("Bet Type (e.g. Spread, Total, Moneyline)")
    amount = st.number_input("Amount Bet ($)", min_value=0.0, step=1.0)
    result = st.selectbox("Result", ["Pending", "Won", "Lost"])

    payout = 0.0
    if result == "Won":
        payout = st.number_input("Payout Received ($)", min_value=0.0, step=1.0)
    elif result == "Lost":
        payout = 0.0
    else:
        payout = ""

    if st.button("💾 Submit Bet"):
        new_data = {
            "Date": date.strftime("%Y-%m-%d"),
            "Event": event,
            "Bet Type": bet_type,
            "Amount": amount,
            "Result": result,
            "Payout": payout
        }
        add_row(sheet, new_data)
        st.success("Bet added!")

with tab2:
    st.subheader("Your Bet History")

    df = get_data(sheet)

    if df.empty:
        st.info("No data available yet.")
    else:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        df["Payout"] = pd.to_numeric(df["Payout"], errors="coerce").fillna(0)

        status_filter = st.multiselect("Filter by Result", options=["Pending", "Won", "Lost"], default=["Pending", "Won", "Lost"])
        filtered_df = df[df["Result"].isin(status_filter)]
        st.dataframe(filtered_df, use_container_width=True)

        # 💵 Profit + Bankroll Stats (only from completed bets)
        completed_bets = df[df["Result"].isin(["Won", "Lost"])]
        total_in = completed_bets["Payout"].sum()
        total_out = completed_bets["Amount"].sum()
        net_profit = total_in - total_out
        current_bankroll = STARTING_BANKROLL + net_profit
        roi = (net_profit / total_out * 100) if total_out > 0 else 0.0

        st.markdown("### 📈 Summary Stats")
        st.markdown(f"💰 **Money In (Winnings):** ${total_in:,.2f}")
        st.markdown(f"📤 **Money Out (All Bets):** ${total_out:,.2f}")
        st.markdown(f"📈 **Net Profit/Loss:** ${net_profit:,.2f}")
        st.markdown(f"🏦 **Current Bankroll:** ${current_bankroll:,.2f} (Starting: ${STARTING_BANKROLL})")
        st.markdown(f"📊 **ROI:** {roi:.2f}%")


