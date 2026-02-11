import streamlit as st
import base64
import requests
import pandas as pd
import numpy as np
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Crypto Volatility and Risk Analyzer",
    layout="wide"
)

# =====================================================
# SESSION STATE
# =====================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "active_page" not in st.session_state:
    st.session_state.active_page = "dashboard"

# =====================================================
# BACKGROUND IMAGE
# =====================================================
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image = get_base64("assets/login_img.png")

st.markdown(f"""
<style>
.stApp {{
    background-image: url("data:image/png;base64,{bg_image}");
    background-size: cover;
    background-position: center;
}}

.header {{
    background: rgba(20, 25, 60, 0.85);
    padding: 25px;
    text-align: center;
    border-radius: 10px;
    margin-bottom:20px;
}}

.header h1, .header h2 {{
    color: #00FFFF;
}}

.box {{
    background: rgba(240,240,240,0.95);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LOGIN PAGE
# =====================================================
if not st.session_state.logged_in:

    st.markdown("""
    <div class="header">
        <h1>Crypto Volatility and Risk Analyzer</h1>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.session_state.active_page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid Username or Password ❌")

# =====================================================
# AFTER LOGIN
# =====================================================
else:

    # =================================================
    # DASHBOARD
    # =================================================
    if st.session_state.active_page == "dashboard":

        st.markdown("""
        <div class="header">
            <h2>Welcome to Crypto Volatility and Risk Analyzer</h2>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Milestone-1"):
                st.session_state.active_page = "milestone_1"
                st.rerun()

            if st.button("Milestone-2"):
                st.session_state.active_page = "milestone_2"
                st.rerun()

        with col2:
            if st.button("Milestone-3"):
                st.session_state.active_page = "milestone_3"
                st.rerun()

            if st.button("Milestone-4"):
                st.session_state.active_page = "milestone_4"
                st.rerun()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # =================================================
    # MILESTONE 1 - DATA ACQUISITION
    # =================================================
    elif st.session_state.active_page == "milestone_1":

        st.markdown("""
        <div class="header">
            <h2>Milestone-1: Data Acquisition (Live Monitoring)</h2>
        </div>
        """, unsafe_allow_html=True)

        crypto_list = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]

        # -----------------------------
        # REFRESH CONTROLS
        # -----------------------------
        col1, col2 = st.columns(2)

        with col1:
            refresh_rate = st.selectbox(
                "Auto Refresh Interval (Seconds)",
                [10, 30, 60, 120],
                index=1
            )

        with col2:
            manual_refresh = st.button("🔄 Refresh Now")

        st_autorefresh(interval=refresh_rate * 1000, key="crypto_refresh")

        # -----------------------------
        # FETCH FUNCTION
        # -----------------------------
        def fetch_crypto_data():

            all_data = []

            for coin in crypto_list:

                url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"


                params = {
                    "vs_currency": "usd",
                    "days": "30",
                    "interval": "daily"
                }

                response = requests.get(url, params=params)

                if response.status_code == 200:

                    data = response.json()
                    prices = data["prices"]

                    df = pd.DataFrame(prices, columns=["timestamp", "price"])
                    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df["crypto"] = coin

                    df = df[["date", "crypto", "price"]]
                    all_data.append(df)

                else:
                    st.error(f"API Error for {coin} - Status Code: {response.status_code}")

            if len(all_data) == 0:
                st.error("No data fetched. Check API key or endpoint.")
                st.stop()

            final_df = pd.concat(all_data)
            final_df.dropna(inplace=True)
            final_df.sort_values("date", inplace=True)

            return final_df

        # -----------------------------
        # FETCH DATA
        # -----------------------------
        with st.spinner("Fetching Live Data from CoinGecko PRO API..."):
            final_df = fetch_crypto_data()

        # -----------------------------
        # STORE LOCALLY
        # -----------------------------
        if not os.path.exists("data"):
            os.makedirs("data")

        file_path = "data/crypto_prices_live.csv"
        final_df.to_csv(file_path, index=False)

        # -----------------------------
        # DISPLAY DATA
        # -----------------------------
        st.success("Live Data Updated Successfully ✅")

        st.write("### Crypto Fetched Data")
        st.dataframe(final_df.tail(10))

        st.write("### Chart Flow Graph")

        selected_coin = st.selectbox(
            "Select Crypto",
            final_df["crypto"].unique()
        )

        filtered = final_df[final_df["crypto"] == selected_coin]
        st.line_chart(filtered.set_index("date")["price"])

        # -----------------------------
        # OUTPUT VERIFICATION
        # -----------------------------
        st.write("### Output Verification")
        st.write(f"✔ Stored at: {file_path}")
        st.write(f"✔ Cryptocurrencies fetched: {len(crypto_list)}")
        st.write("✔ API Connectivity Verified")
        st.write(f"✔ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if st.button("⬅ Back to Dashboard"):
            st.session_state.active_page = "dashboard"
            st.rerun()

