import streamlit as st
import base64
import requests
import pandas as pd
import numpy as np
import os
import time
import plotly.graph_objects as go
import plotly.express as px
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

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "users_db" not in st.session_state:
    st.session_state.users_db = {"admin": "admin"}

# ⭐ NEW — selected days state
if "selected_days" not in st.session_state:
    st.session_state.selected_days = 180

# =====================================================
# BACKGROUND IMAGE
# =====================================================
def get_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

bg_image = get_base64("assets/login_img.png")

# =====================================================
# PREMIUM UI (UPDATED WITH MILESTONE STYLING)
# =====================================================
if bg_image:
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(5, 8, 25, 0.75);
        z-index: -1;
    }}
    .header {{
        background: rgba(15, 20, 45, 0.90);
        padding: 25px;
        text-align: center;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    .header h1, .header h2 {{
        color: #00FFFF;
        text-shadow: 0 0 10px rgba(0,255,255,0.5);
    }}
    .stButton>button {{
        background-color: #00FFFF;
        color: black;
        font-weight: bold;
        border-radius: 8px;
        border: 2px solid #00FFFF;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #00CCCC;
        color: white;
        box-shadow: 0 0 20px rgba(0,255,255,0.5);
    }}
    
    /* ⭐ MILESTONE LABELS */
    .milestone-label {{
        color: #00FFFF !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        margin-bottom: 10px !important;
    }}
    
    .metric-label {{
        color: #00FFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }}
    
    .metric-value {{
        font-size: 28px !important;
        font-weight: bold !important;
    }}
    
    .volatility-value {{
        color: #00FF00 !important;  /* Green for volatility */
    }}
    
    .risk-value {{
        color: #FFD700 !important;  /* Gold for risk */
    }}
    
    .milestone-subheader {{
        color: #00FFFF !important;
        font-weight: 700 !important;
        font-size: 18px !important;
    }}
    
    /* ⭐ UPDATED AUTH BOX */
    .auth-box {{
        max-width: 450px;
        margin: 50px auto;
        padding: 40px;
        background: rgba(15, 20, 45, 0.98);
        border: 2px solid #00FFFF;
        border-radius: 20px;
        box-shadow: 0 0 40px rgba(0,255,255,0.3), 
                    inset 0 0 20px rgba(0,255,255,0.1);
        backdrop-filter: blur(10px);
    }}
    .auth-title {{
        text-align: center;
        color: #00FFFF;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 30px;
        text-shadow: 0 0 10px rgba(0,255,255,0.5);
    }}
    /* ⭐ UPDATED INPUT LABELS - CYAN COLOR */
    .stTextInput > label {{
        color: #00FFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }}
    .stTextInput > div > div > input {{
        background-color: rgba(20, 30, 60, 0.9) !important;
        border: 1.5px solid #00FFFF !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #00FFFF !important;
        box-shadow: 0 0 10px rgba(0,255,255,0.5) !important;
    }}
    .stTextInput > div > div > input::placeholder {{
        color: rgba(0, 255, 255, 0.5) !important;
    }}
    /* ⭐ INPUT TEXT COLOR */
    .stTextInput input {{
        color: #FFFFFF !important;
    }}
    /* Button Styling */
    .auth-box .stButton > button {{
        width: 100%;
        padding: 12px;
        margin-top: 10px;
        font-size: 16px;
    }}
    .auth-box .stButton > button:first-of-type {{
        background: linear-gradient(135deg, #00FFFF, #00CCCC);
        box-shadow: 0 0 20px rgba(0,255,255,0.4);
    }}
    .auth-error {{
        background-color: rgba(255, 50, 50, 0.2) !important;
        border-left: 4px solid #FF3333 !important;
        color: #FF6666 !important;
        padding: 12px !important;
        border-radius: 8px !important;
    }}
    .auth-success {{
        background-color: rgba(50, 255, 100, 0.2) !important;
        border-left: 4px solid #33FF66 !important;
        color: #66FF99 !important;
        padding: 12px !important;
        border-radius: 8px !important;
    }}
    /* Warning/Info Styling */
    .stAlert {{
        background-color: rgba(255, 200, 50, 0.2) !important;
        border-left: 4px solid #FFCC00 !important;
        color: #FFDD66 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def calculate_volatility_simple(df):
    if df.empty or len(df) < 2:
        return 0
    returns = df["price"].pct_change().dropna()
    return returns.std() * np.sqrt(365) * 100

def risk_level(vol):
    if vol < 20:
        return "🟢 Low Risk"
    elif vol < 50:
        return "🟡 Medium Risk"
    else:
        return "🔴 High Risk"

# =====================================================
# BINANCE FETCH (UPDATED)
# =====================================================
BINANCE_BASE_URLS = [
    "https://api.binance.com",
    "https://api-gcp.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
]

crypto_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT"]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_binance_data(days):
    limit = min(days, 1000)
    all_data = []

    for symbol in crypto_symbols:
        for base_url in BINANCE_BASE_URLS:
            try:
                url = f"{base_url}/api/v3/klines"
                params = {
                    "symbol": symbol,
                    "interval": "1d",
                    "limit": limit
                }

                r = requests.get(url, params=params, timeout=10)

                if r.status_code == 200:
                    df = pd.DataFrame(r.json())
                    df = df.iloc[:, [0, 4]]
                    df.columns = ["timestamp", "price"]
                    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df["crypto"] = symbol
                    df["price"] = df["price"].astype(float)
                    all_data.append(df[["date", "crypto", "price"]])
                    break
            except Exception:
                continue
        time.sleep(0.2)

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data).sort_values("date")

# =====================================================
# MILESTONE 2 FUNCTIONS (UNCHANGED)
# =====================================================
TRADING_DAYS = 252

def validate_price_data(df):
    required_cols = {"date", "crypto", "price"}
    return not df.empty and required_cols.issubset(df.columns)

def compute_log_returns(df):
    df = df.copy().sort_values(["crypto", "date"])
    df["log_return"] = df.groupby("crypto")["price"].transform(
        lambda x: np.log(x / x.shift(1))
    )
    return df

def compute_volatility(returns_df):
    return (returns_df.groupby("crypto")["log_return"]
            .std() * np.sqrt(TRADING_DAYS) * 100).round(2)

def compute_sharpe(returns_df):
    mean_returns = returns_df.groupby("crypto")["log_return"].mean() * TRADING_DAYS
    vol = returns_df.groupby("crypto")["log_return"].std() * np.sqrt(TRADING_DAYS)
    return (mean_returns / vol).round(2)

def compute_beta(returns_df, benchmark="BTCUSDT"):
    pivot = returns_df.pivot(index="date", columns="crypto", values="log_return")
    if benchmark not in pivot.columns:
        return pd.Series(dtype=float)

    market_var = pivot[benchmark].var()
    beta_values = {}

    for col in pivot.columns:
        if col == benchmark:
            beta_values[col] = 1.0
        else:
            cov = pivot[col].cov(pivot[benchmark])
            beta_values[col] = cov / market_var if market_var != 0 else np.nan

    return pd.Series(beta_values).round(2)

def add_rolling_features(df, window=30):
    df = df.copy().sort_values(["crypto", "date"])
    df["ma_30"] = df.groupby("crypto")["price"].transform(
        lambda x: x.rolling(window).mean()
    )
    df["rolling_vol_30"] = df.groupby("crypto")["log_return"].transform(
        lambda x: x.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100
    )
    return df

def build_metrics_table(returns_df):
    metrics = pd.concat([
        compute_volatility(returns_df),
        compute_sharpe(returns_df),
        compute_beta(returns_df)
    ], axis=1)
    metrics.columns = ["Volatility (%)", "Sharpe Ratio", "Beta vs BTC"]
    return metrics.reset_index().rename(columns={"index": "Crypto"})

# =====================================================
# LOGIN PAGE (UPDATED)
# =====================================================
if not st.session_state.logged_in:

    st.markdown(
        '<div class="header"><h1>🔐 Crypto Volatility & Risk Analyzer</h1></div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="auth-box">', unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":

        st.markdown('<div class="auth-title">🔓 Login</div>', unsafe_allow_html=True)

        username = st.text_input("👤 Username", key="login_user", placeholder="Enter your username")
        password = st.text_input("🔑 Password", type="password", key="login_pass", placeholder="Enter your password")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Login", use_container_width=True):
                if username in st.session_state.users_db and \
                   st.session_state.users_db[username] == password:
                    st.session_state.logged_in = True
                    st.success("✨ Login Successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")

        with col2:
            if st.button("📝 Register", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()

    else:
        # REGISTER MODE
        st.markdown('<div class="auth-title">📝 Create Account</div>', unsafe_allow_html=True)

        new_user = st.text_input("👤 Create Username", key="reg_user", placeholder="Choose a username")
        new_pass = st.text_input("🔑 Create Password", type="password", key="reg_pass", placeholder="Create a strong password")
        confirm_pass = st.text_input("🔐 Confirm Password", type="password", key="confirm_pass", placeholder="Re-enter password")

        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Register", use_container_width=True):

                if not new_user or not new_pass:
                    st.warning("⚠️ Please fill all fields")
                elif new_user in st.session_state.users_db:
                    st.error("❌ Username already exists")
                elif new_pass != confirm_pass:
                    st.error("❌ Passwords do not match")
                elif len(new_pass) < 4:
                    st.error("❌ Password must be at least 4 characters")
                else:
                    st.session_state.users_db[new_user] = new_pass
                    st.success("✨ Account created successfully!")
                    st.session_state.auth_mode = "login"
                    time.sleep(1)
                    st.rerun()

        with col2:
            if st.button("⬅️ Back to Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #00FFFF; margin-top: 50px; opacity: 0.7;'>
        <p>🚀 Advanced Crypto Risk Analysis Platform</p>
        <p style='font-size: 12px;'>Demo Credentials: admin / admin</p>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# MAIN APP
# =====================================================
else:

    if st.session_state.active_page == "dashboard":

        st.markdown(
            '<div class="header"><h2>👋 Welcome Dashboard</h2></div>',
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 Data Acquisition", use_container_width=True):
                st.session_state.active_page = "milestone_1"
                st.rerun()

        with col2:
            if st.button("📈 Data Processing", use_container_width=True):
                st.session_state.active_page = "milestone_2"
                st.rerun()

        with col3:
            if st.button("🧩 Milestone-3", use_container_width=True):
                st.session_state.active_page = "milestone_3"
                st.rerun()

        with col4:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

    # =================================================
    # MILESTONE 1 (UPDATED WITH CYAN TEXT)
    # =================================================
    elif st.session_state.active_page == "milestone_1":

        st_autorefresh(interval=60000, key="datarefresh")

        st.markdown(
            '<div class="header"><h2>📊 Milestone-1: Live Crypto Monitoring</h2></div>',
            unsafe_allow_html=True
        )

        # ⭐ CONTROLS WITH CYAN LABELS
        cA, cB = st.columns([1, 1])

        with cA:
            st.markdown(
                '<p class="milestone-label">📅 Select Data Range</p>',
                unsafe_allow_html=True
            )
            days = st.selectbox(
                "label",
                [30, 180, 365],
                index=[30, 180, 365].index(st.session_state.selected_days),
                label_visibility="collapsed"
            )
            st.session_state.selected_days = days

        with cB:
            if st.button("🔄 Refresh Data", use_container_width=True):
                fetch_binance_data.clear()
                st.rerun()

        with st.spinner("⏳ Fetching Binance data..."):
            final_df = fetch_binance_data(st.session_state.selected_days)

        if final_df.empty:
            st.error("⚠️ Binance API unavailable - Please try again later")
            st.stop()

        os.makedirs("data", exist_ok=True)
        file_path = "data/binance_crypto_prices.csv"
        final_df.to_csv(file_path, index=False)

        st.success("✅ Live Data Updated Successfully!")
        
        st.markdown(
            '<p class="milestone-subheader">📋 Recent Data (Last 10 Records)</p>',
            unsafe_allow_html=True
        )
        st.dataframe(final_df.tail(10), use_container_width=True)

        # ⭐ CYAN TEXT FOR "Select Cryptocurrency"
        st.markdown(
            '<p class="milestone-label">🔍 Select Cryptocurrency</p>',
            unsafe_allow_html=True
        )
        selected_coin = st.selectbox(
            "label",
            final_df["crypto"].unique(),
            label_visibility="collapsed"
        )

        filtered = final_df[final_df["crypto"] == selected_coin]
        
        st.markdown(
            '<p class="milestone-subheader">📈 Price Chart</p>',
            unsafe_allow_html=True
        )
        st.line_chart(filtered.set_index("date")["price"], use_container_width=True)

        vol = calculate_volatility_simple(filtered)
        risk = risk_level(vol)

        # ⭐ CYAN LABELS FOR METRICS WITH COLORED VALUES
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown(
                '<p class="metric-label">📊 Volatility (Annualized)</p>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<p class="metric-value volatility-value">{vol:.2f}%</p>',
                unsafe_allow_html=True
            )
        
        with c2:
            st.markdown(
                '<p class="metric-label">⚠️ Risk Level</p>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<p class="metric-value risk-value">{risk}</p>',
                unsafe_allow_html=True
            )

        st.divider()
        
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.active_page = "dashboard"
            st.rerun()

    # =================================================
    # MILESTONE 3 (NEW)
    # =================================================
    elif st.session_state.active_page == "milestone_3":

        st.markdown(
            '<div class="header"><h2>🧩 Milestone-3: Time-Series & Risk-Return Dashboard</h2></div>',
            unsafe_allow_html=True
        )

        st.markdown('<p class="milestone-subheader">📁 Loading / Preparing Processed Data</p>', unsafe_allow_html=True)

        def load_or_build_processed():
            proc_path = "data/crypto_processed.csv"
            raw_path = "data/binance_crypto_prices.csv"

            if os.path.exists(proc_path):
                try:
                    df = pd.read_csv(proc_path, parse_dates=["Date"]) 
                    expected = {"Date", "Close", "Returns", "Volatility", "Sharpe_Ratio", "Crypto"}
                    if expected.issubset(set(df.columns)):
                        return df
                except Exception:
                    pass

            # Fallback: build from raw Binance CSV
            if not os.path.exists(raw_path):
                return pd.DataFrame()

            df = pd.read_csv(raw_path)
            df = df.rename(columns={"date": "Date", "price": "Close", "crypto": "Crypto"})
            df["Date"] = pd.to_datetime(df["Date"]) 
            df = df.sort_values(["Crypto", "Date"]).reset_index(drop=True)
            df["Close"] = df["Close"].astype(float)
            df["Returns"] = df.groupby("Crypto")["Close"].transform(lambda x: x.pct_change())
            # Rolling volatility and Sharpe (30-day window)
            window = 30
            df["Volatility"] = df.groupby("Crypto")["Returns"].transform(
                lambda x: x.rolling(window).std() * np.sqrt(TRADING_DAYS)
            )
            df["Sharpe_Ratio"] = df.groupby("Crypto")["Returns"].transform(
                lambda x: (x.rolling(window).mean() * TRADING_DAYS) / (x.rolling(window).std() * np.sqrt(TRADING_DAYS))
            )

            # Keep mandatory columns and save a copy for faster reloads
            out = df[["Date", "Crypto", "Close", "Returns", "Volatility", "Sharpe_Ratio"]]
            try:
                out.to_csv(proc_path, index=False)
            except Exception:
                pass

            return out

        proc_df = load_or_build_processed()

        if proc_df.empty:
            st.error("⚠️ Processed dataset not found and raw data unavailable. Run Milestone-1 & Milestone-2 first.")
            if st.button("⬅️ Back to Dashboard", use_container_width=True):
                st.session_state.active_page = "dashboard"
                st.rerun()
            st.stop()

        # -----------------------
        # Filters
        # -----------------------
        min_date = proc_df["Date"].min().date()
        max_date = proc_df["Date"].max().date()

        c1, c2 = st.columns([2, 3])
        with c1:
            date_range = st.date_input("Select date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            cryptos = st.multiselect("Select cryptocurrencies", options=proc_df["Crypto"].unique(), default=list(proc_df["Crypto"].unique()))

        with c2:
            st.markdown("\n")
            if st.button("🔄 Refresh Processed Data", use_container_width=True):
                # clear cache file and rebuild
                try:
                    if os.path.exists("data/crypto_processed.csv"):
                        os.remove("data/crypto_processed.csv")
                except Exception:
                    pass
                proc_df = load_or_build_processed()
                st.experimental_rerun()

        # -----------------------
        # Data filtering
        # -----------------------
        start, end = date_range
        mask = (proc_df["Date"].dt.date >= start) & (proc_df["Date"].dt.date <= end) & (proc_df["Crypto"].isin(cryptos))
        filtered = proc_df.loc[mask].copy()

        if filtered.empty:
            st.warning("No data for selected filters")
        else:
            # -----------------------
            # Price Trend
            # -----------------------
            st.markdown('<p class="milestone-subheader">📈 Price Trend</p>', unsafe_allow_html=True)
            fig_price = px.line(filtered, x="Date", y="Close", color="Crypto", title="Price vs Date")
            fig_price.update_layout(plot_bgcolor="rgba(15, 20, 45, 0.5)", paper_bgcolor="rgba(15, 20, 45, 0.3)", font=dict(color="#00FFFF"))
            st.plotly_chart(fig_price, use_container_width=True)

            # -----------------------
            # Volatility Trend
            # -----------------------
            st.markdown('<p class="milestone-subheader">📉 Volatility Trend</p>', unsafe_allow_html=True)
            fig_vol = px.line(filtered, x="Date", y="Volatility", color="Crypto", title="Volatility vs Date")
            fig_vol.update_layout(plot_bgcolor="rgba(15, 20, 45, 0.5)", paper_bgcolor="rgba(15, 20, 45, 0.3)", font=dict(color="#00FFFF"))
            st.plotly_chart(fig_vol, use_container_width=True)

            # -----------------------
            # Risk-Return Scatter
            # -----------------------
            st.markdown('<p class="milestone-subheader">⚖️ Risk–Return Scatter</p>', unsafe_allow_html=True)
            grp = filtered.groupby("Crypto").agg(
                Average_Return=("Returns", lambda x: x.mean() * TRADING_DAYS * 100),
                Average_Volatility=("Volatility", "mean"),
                Avg_Sharpe=("Sharpe_Ratio", "mean")
            ).reset_index()

            fig_scatter = px.scatter(grp, x="Average_Volatility", y="Average_Return", color="Crypto", size_max=40, hover_data=["Avg_Sharpe"], title="Risk vs Return")
            fig_scatter.update_layout(plot_bgcolor="rgba(15, 20, 45, 0.5)", paper_bgcolor="rgba(15, 20, 45, 0.3)", font=dict(color="#00FFFF"))
            fig_scatter.update_xaxes(title_text="Volatility (%)")
            fig_scatter.update_yaxes(title_text="Annualized Return (%)")
            st.plotly_chart(fig_scatter, use_container_width=True)

            # -----------------------
            # KPIs
            # -----------------------
            st.markdown('<p class="milestone-subheader">📊 KPIs</p>', unsafe_allow_html=True)
            kpi_grp = filtered.groupby("Crypto").agg(
                Volatility=("Volatility", "mean"),
                Return=("Returns", lambda x: x.mean() * TRADING_DAYS * 100),
                Sharpe=("Sharpe_Ratio", "mean")
            ).round(2).reset_index()

            st.dataframe(kpi_grp, use_container_width=True)

        st.divider()

        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.active_page = "dashboard"
            st.rerun()

    # =================================================
    # MILESTONE 2 (UPDATED WITH CYAN TEXT)
    # =================================================
    elif st.session_state.active_page == "milestone_2":

        st.markdown(
            '<div class="header"><h2>📈 Milestone-2: Data Processing & Analysis</h2></div>',
            unsafe_allow_html=True
        )

        # ⭐ NEW refresh control
        cA, cB = st.columns([1, 1])

        with cA:
            st.info(f"📅 Using last **{st.session_state.selected_days} days** of data")

        with cB:
            if st.button("🔄 Refresh Metrics", use_container_width=True):
                fetch_binance_data.clear()
                st.rerun()

        file_path = "data/binance_crypto_prices.csv"

        if not os.path.exists(file_path):
            st.error("⚠️ Run Milestone-1 first to acquire data.")
            st.stop()

        price_df = pd.read_csv(file_path)
        price_df["date"] = pd.to_datetime(price_df["date"])

        if not validate_price_data(price_df):
            st.error("❌ Invalid dataset")
            st.stop()

        with st.spinner("⏳ Computing metrics..."):
            returns_df = compute_log_returns(price_df)
            returns_df = add_rolling_features(returns_df)
            metrics_df = build_metrics_table(returns_df)

        st.success("✅ Metrics computed successfully!")

        st.markdown(
            '<p class="milestone-subheader">📊 Risk Metrics Table</p>',
            unsafe_allow_html=True
        )
        st.dataframe(metrics_df, use_container_width=True)

        st.markdown(
            '<p class="milestone-subheader">📉 Volatility Comparison</p>',
            unsafe_allow_html=True
        )
        fig_bar = px.bar(
            metrics_df,
            x="Crypto",
            y="Volatility (%)",
            color="Volatility (%)",
            color_continuous_scale="Viridis",
            title="Volatility Across Cryptocurrencies"
        )
        fig_bar.update_layout(
            plot_bgcolor="rgba(15, 20, 45, 0.5)",
            paper_bgcolor="rgba(15, 20, 45, 0.3)",
            font=dict(color="#00FFFF")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown(
            '<p class="milestone-subheader">📈 Rolling Volatility (30-Day)</p>',
            unsafe_allow_html=True
        )

        selected_crypto = st.selectbox(
            "🔍 Select Cryptocurrency for Rolling Analysis",
            returns_df["crypto"].unique()
        )

        temp = returns_df[returns_df["crypto"] == selected_crypto]

        fig_roll = px.line(
            temp, 
            x="date", 
            y="rolling_vol_30",
            title=f"30-Day Rolling Volatility - {selected_crypto}",
            labels={"rolling_vol_30": "Volatility (%)", "date": "Date"}
        )
        fig_roll.update_layout(
            plot_bgcolor="rgba(15, 20, 45, 0.5)",
            paper_bgcolor="rgba(15, 20, 45, 0.3)",
            font=dict(color="#00FFFF")
        )
        st.plotly_chart(fig_roll, use_container_width=True)

        st.divider()

        # Key Insights
        most_volatile = metrics_df.loc[
            metrics_df["Volatility (%)"].idxmax(), "Crypto"
        ]
        best_sharpe = metrics_df.loc[
            metrics_df["Sharpe Ratio"].idxmax(), "Crypto"
        ]
        
        lowest_beta = metrics_df.loc[
            metrics_df["Beta vs BTC"].idxmin(), "Crypto"
        ]
        highest_beta = metrics_df.loc[
            metrics_df["Beta vs BTC"].idxmax(), "Crypto"
        ]

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"<p style='color: #FF6B6B; font-weight: bold; text-align: center;'>🔥 Most Volatile<br>{most_volatile}</p>",
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"<p style='color: #51CF66; font-weight: bold; text-align: center;'>🏆 Best Sharpe<br>{best_sharpe}</p>",
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"<p style='color: #74C0FC; font-weight: bold; text-align: center;'>📉 Lowest Beta<br>{lowest_beta}</p>",
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f"<p style='color: #FFD700; font-weight: bold; text-align: center;'>📈 Highest Beta<br>{highest_beta}</p>",
                unsafe_allow_html=True
            )

        st.divider()

        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.active_page = "dashboard"
            st.rerun()
