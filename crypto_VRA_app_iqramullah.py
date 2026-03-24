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

# NEW IMPORTS FOR MILESTONE-4
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import io
from PIL import Image as PILImage
import json

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

if "selected_days" not in st.session_state:
    st.session_state.selected_days = 180

if "risk_thresholds" not in st.session_state:
    st.session_state.risk_thresholds = {
        "low": 20,
        "medium": 50,
        "high": float('inf')
    }

if "sharpe_thresholds" not in st.session_state:
    st.session_state.sharpe_thresholds = {
        "excellent": 2.0,
        "good": 1.0,
        "acceptable": 0.5,
        "poor": float('-inf')
    }

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
        color: #00FF00 !important;
    }}
    
    .risk-value {{
        color: #FFD700 !important;
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
    
    .stTextInput input {{
        color: #FFFFFF !important;
    }}
    
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
    
    /* Risk classification styles */
    .risk-low {{
        background-color: rgba(50, 255, 100, 0.15) !important;
        border-left: 4px solid #33FF66 !important;
        color: #66FF99 !important;
    }}
    
    .risk-medium {{
        background-color: rgba(255, 200, 50, 0.15) !important;
        border-left: 4px solid #FFCC00 !important;
        color: #FFDD66 !important;
    }}
    
    .risk-high {{
        background-color: rgba(255, 50, 50, 0.15) !important;
        border-left: 4px solid #FF3333 !important;
        color: #FF6666 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# =====================================================
# GLOBAL HELPER FUNCTIONS
# =====================================================

def calculate_volatility_simple(df):
    """Calculate simple volatility from price data"""
    if df.empty or len(df) < 2:
        return 0
    returns = df["price"].pct_change().dropna()
    if returns.empty or returns.std() == 0:
        return 0
    return returns.std() * np.sqrt(365) * 100

def risk_level(vol):
    """Classify risk level from volatility"""
    if vol < 20:
        return "🟢 Low Risk"
    elif vol < 50:
        return "🟡 Medium Risk"
    else:
        return "🔴 High Risk"

# =====================================================
# ⭐ MILESTONE-2: DATA PROCESSING FUNCTIONS
# =====================================================
TRADING_DAYS = 252

def validate_price_data(df):
    """Validate price dataset has required columns"""
    required_cols = {"date", "crypto", "price"}
    return not df.empty and required_cols.issubset(df.columns)

def compute_log_returns(df):
    """Compute log returns from price data"""
    df = df.copy().sort_values(["crypto", "date"])
    df["log_return"] = df.groupby("crypto")["price"].transform(
        lambda x: np.log(x / x.shift(1))
    )
    return df

def compute_volatility(returns_df):
    """Compute annualized volatility"""
    return (returns_df.groupby("crypto")["log_return"]
            .std() * np.sqrt(TRADING_DAYS) * 100).round(2)

def compute_sharpe(returns_df):
    """Compute Sharpe Ratio"""
    mean_returns = returns_df.groupby("crypto")["log_return"].mean() * TRADING_DAYS
    vol = returns_df.groupby("crypto")["log_return"].std() * np.sqrt(TRADING_DAYS)
    return (mean_returns / vol).round(2)

def compute_beta(returns_df, benchmark="BTCUSDT"):
    """Compute Beta vs benchmark"""
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
    """Add rolling volatility and moving average"""
    df = df.copy().sort_values(["crypto", "date"])
    df["ma_30"] = df.groupby("crypto")["price"].transform(
        lambda x: x.rolling(window).mean()
    )
    df["rolling_vol_30"] = df.groupby("crypto")["log_return"].transform(
        lambda x: x.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100
    )
    return df

def build_metrics_table(returns_df):
    """Build comprehensive metrics table"""
    metrics = pd.concat([
        compute_volatility(returns_df),
        compute_sharpe(returns_df),
        compute_beta(returns_df)
    ], axis=1)
    metrics.columns = ["Volatility (%)", "Sharpe Ratio", "Beta vs BTC"]
    return metrics.reset_index().rename(columns={"index": "Crypto"})

# =====================================================
# ⭐ MILESTONE-4: RISK CLASSIFICATION HELPERS
# =====================================================

def classify_risk_level(volatility, thresholds=None):
    """Classify risk level based on volatility percentage"""
    if thresholds is None:
        thresholds = st.session_state.risk_thresholds
    
    if volatility < thresholds["low"]:
        return ("🟢 Low Risk", "🟢", "#33FF66", "risk-low")
    elif volatility < thresholds["medium"]:
        return ("🟡 Medium Risk", "🟡", "#FFCC00", "risk-medium")
    else:
        return ("🔴 High Risk", "🔴", "#FF3333", "risk-high")


def classify_sharpe_ratio(sharpe_ratio, thresholds=None):
    """Classify Sharpe Ratio quality"""
    if thresholds is None:
        thresholds = st.session_state.sharpe_thresholds
    
    if sharpe_ratio >= thresholds["excellent"]:
        return "⭐⭐⭐ Excellent"
    elif sharpe_ratio >= thresholds["good"]:
        return "⭐⭐ Good"
    elif sharpe_ratio >= thresholds["acceptable"]:
        return "⭐ Acceptable"
    else:
        return "❌ Poor"


def generate_risk_report_dataframe(returns_df, metrics_df):
    """Generate comprehensive risk classification report"""
    report = metrics_df.copy()
    
    report["Risk_Level"] = report["Volatility (%)"].apply(classify_risk_level)
    report["Risk_Label"] = report["Risk_Level"].apply(lambda x: x[0])
    report["Risk_Emoji"] = report["Risk_Level"].apply(lambda x: x[1])
    
    report["Sharpe_Quality"] = report["Sharpe Ratio"].apply(classify_sharpe_ratio)
    
    report = report[["Crypto", "Volatility (%)", "Risk_Label", "Sharpe Ratio", "Sharpe_Quality", "Beta vs BTC"]]
    report = report.rename(columns={"Risk_Label": "Risk Classification"})
    
    return report


def create_risk_dashboard_data(filtered_df, metrics_df):
    """Create enriched dashboard data with risk classifications"""
    dashboard_data = {
        "total_cryptos": len(metrics_df),
        "high_risk_count": len(metrics_df[metrics_df["Volatility (%)"] > st.session_state.risk_thresholds["medium"]]),
        "medium_risk_count": len(metrics_df[(metrics_df["Volatility (%)"] >= st.session_state.risk_thresholds["low"]) & 
                                            (metrics_df["Volatility (%)"] <= st.session_state.risk_thresholds["medium"])]),
        "low_risk_count": len(metrics_df[metrics_df["Volatility (%)"] < st.session_state.risk_thresholds["low"]]),
        "avg_volatility": metrics_df["Volatility (%)"].mean(),
        "avg_sharpe": metrics_df["Sharpe Ratio"].mean(),
        "highest_vol_crypto": metrics_df.loc[metrics_df["Volatility (%)"].idxmax(), "Crypto"],
        "highest_vol_value": metrics_df["Volatility (%)"].max(),
        "best_sharpe_crypto": metrics_df.loc[metrics_df["Sharpe Ratio"].idxmax(), "Crypto"],
        "best_sharpe_value": metrics_df["Sharpe Ratio"].max(),
    }
    return dashboard_data


def export_risk_report_csv(report_df, filename="risk_report.csv"):
    """Export risk report to CSV"""
    os.makedirs("reports", exist_ok=True)
    filepath = os.path.join("reports", filename)
    report_df.to_csv(filepath, index=False)
    
    with open(filepath, "rb") as f:
        return f.read()


def generate_risk_report_pdf(report_df, dashboard_data, filename="risk_report.pdf"):
    """Generate comprehensive PDF risk report"""
    os.makedirs("reports", exist_ok=True)
    filepath = os.path.join("reports", filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00FFFF'),
        spaceAfter=30,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#00FFFF'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=6
    )
    
    elements.append(Paragraph("🔐 Crypto Volatility & Risk Analysis Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"<b>Report Generated:</b> {report_date}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("📊 Executive Summary", heading_style))
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Cryptocurrencies Analyzed", str(dashboard_data["total_cryptos"])],
        ["High Risk Assets", str(dashboard_data["high_risk_count"])],
        ["Medium Risk Assets", str(dashboard_data["medium_risk_count"])],
        ["Low Risk Assets", str(dashboard_data["low_risk_count"])],
        ["Average Volatility", f"{dashboard_data['avg_volatility']:.2f}%"],
        ["Average Sharpe Ratio", f"{dashboard_data['avg_sharpe']:.2f}"],
        ["Most Volatile Asset", f"{dashboard_data['highest_vol_crypto']} ({dashboard_data['highest_vol_value']:.2f}%)"],
        ["Best Risk-Adjusted Return", f"{dashboard_data['best_sharpe_crypto']} ({dashboard_data['best_sharpe_value']:.2f})"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00FFFF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(PageBreak())
    elements.append(Paragraph("📋 Detailed Risk Classification Report", heading_style))
    
    table_data = [["Crypto", "Volatility (%)", "Risk Level", "Sharpe Ratio", "Sharpe Quality", "Beta vs BTC"]]
    
    for _, row in report_df.iterrows():
        table_data.append([
            str(row["Crypto"]),
            f"{row['Volatility (%)']:.2f}",
            row["Risk Classification"],
            f"{row['Sharpe Ratio']:.2f}",
            str(row["Sharpe_Quality"]),
            f"{row['Beta vs BTC']:.2f}"
        ])
    
    detail_table = Table(table_data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 1*inch, 1.2*inch, 1*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00FFFF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(detail_table)
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("⚙️ Risk Classification Thresholds", heading_style))
    
    threshold_data = [
        ["Risk Level", "Volatility Range"],
        ["🟢 Low Risk", f"< {st.session_state.risk_thresholds['low']}%"],
        ["🟡 Medium Risk", f"{st.session_state.risk_thresholds['low']}% - {st.session_state.risk_thresholds['medium']}%"],
        ["🔴 High Risk", f"> {st.session_state.risk_thresholds['medium']}%"],
    ]
    
    threshold_table = Table(threshold_data, colWidths=[2.5*inch, 3.5*inch])
    threshold_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00FFFF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(threshold_table)
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("💡 Recommendations", heading_style))
    
    recommendations = f"""
    <b>Portfolio Risk Assessment:</b><br/>
    • High-risk assets ({dashboard_data['high_risk_count']}) should be monitored closely for volatility changes<br/>
    • Consider diversification with low-risk assets ({dashboard_data['low_risk_count']})<br/>
    • Review Sharpe ratios to identify best risk-adjusted opportunities<br/>
    <br/>
    <b>Key Insights:</b><br/>
    • Most volatile asset: {dashboard_data['highest_vol_crypto']} ({dashboard_data['highest_vol_value']:.2f}% volatility)<br/>
    • Best risk-adjusted return: {dashboard_data['best_sharpe_crypto']} (Sharpe: {dashboard_data['best_sharpe_value']:.2f})<br/>
    • Portfolio average volatility: {dashboard_data['avg_volatility']:.2f}%<br/>
    """
    
    elements.append(Paragraph(recommendations, normal_style))
    
    doc.build(elements)
    
    with open(filepath, "rb") as f:
        return f.read()


def create_plotly_risk_gauge(risk_level_name, value):
    """Create a gauge chart for risk visualization"""
    colors_map = {
        "Low": "#33FF66",
        "Medium": "#FFCC00",
        "High": "#FF3333"
    }
    
    risk_type = "Low" if value < 20 else ("Medium" if value < 50 else "High")
    color = colors_map[risk_type]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Volatility %"},
        delta={'reference': 30},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 20], 'color': "rgba(51, 255, 102, 0.3)"},
                {'range': [20, 50], 'color': "rgba(255, 204, 0, 0.3)"},
                {'range': [50, 100], 'color': "rgba(255, 51, 51, 0.3)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        plot_bgcolor="rgba(15, 20, 45, 0.5)",
        paper_bgcolor="rgba(15, 20, 45, 0.3)",
        font=dict(color="#00FFFF"),
        height=250
    )
    
    return fig


def create_risk_distribution_chart(metrics_df):
    """Create pie chart for risk distribution"""
    low_count = len(metrics_df[metrics_df["Volatility (%)"] < st.session_state.risk_thresholds["low"]])
    med_count = len(metrics_df[(metrics_df["Volatility (%)"] >= st.session_state.risk_thresholds["low"]) & 
                               (metrics_df["Volatility (%)"] <= st.session_state.risk_thresholds["medium"])])
    high_count = len(metrics_df[metrics_df["Volatility (%)"] > st.session_state.risk_thresholds["medium"]])
    
    labels = ["🟢 Low Risk", "🟡 Medium Risk", "🔴 High Risk"]
    values = [low_count, med_count, high_count]
    colors_list = ["#33FF66", "#FFCC00", "#FF3333"]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors_list),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Risk Distribution",
        plot_bgcolor="rgba(15, 20, 45, 0.5)",
        paper_bgcolor="rgba(15, 20, 45, 0.3)",
        font=dict(color="#00FFFF"),
        height=250
    )
    
    return fig

# =====================================================
# BINANCE FETCH (MILESTONE 1)
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
    """Fetch cryptocurrency price data from Binance API"""
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
                    df["date"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
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
# LOGIN PAGE
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

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("📊 Data Acquisition", use_container_width=True):
                st.session_state.active_page = "milestone_1"
                st.rerun()

        with col2:
            if st.button("📈 Data Processing", use_container_width=True):
                st.session_state.active_page = "milestone_2"
                st.rerun()

        with col3:
            if st.button("🧩 Visualization", use_container_width=True):
                st.session_state.active_page = "milestone_3"
                st.rerun()

        with col4:
            if st.button("📋 Risk Report", use_container_width=True):
                st.session_state.active_page = "milestone_4"
                st.rerun()

        with col5:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

    # =====================================================
    # ⭐ MILESTONE 1: DATA ACQUISITION (UPDATED UI)
    # =====================================================
    elif st.session_state.active_page == "milestone_1":

        st_autorefresh(interval=60000, key="datarefresh")

        st.markdown(
            '<div class="header"><h2>📊 Milestone-1: Data Acquisition</h2></div>',
            unsafe_allow_html=True
        )

        # =====================================================
        # SECTION 1: CONTROLS (LEFT-RIGHT LAYOUT)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">⚙️ Data Configuration</p>',
            unsafe_allow_html=True
        )
        
        col_left, col_right = st.columns([1, 1], gap="large")

        # LEFT COLUMN: DATE RANGE SELECTION
        with col_left:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 20px; border-radius: 10px; border-left: 4px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 16px; margin-bottom: 12px;'>📅 SELECT TIME PERIOD</p>
            </div>
            """, unsafe_allow_html=True)
            
            days = st.radio(
                "Choose data range:",
                [30, 180, 365],
                format_func=lambda x: {
                    30: "📆 Last 30 Days",
                    180: "📊 Last 6 Months (Recommended)",
                    365: "📈 Last 1 Year"
                }[x],
                key="days_radio",
                index={30: 0, 180: 1, 365: 2}[st.session_state.selected_days]
            )
            st.session_state.selected_days = days
            
            # Display selected range info
            st.markdown(f"""
            <div style='background: rgba(0, 255, 255, 0.1); padding: 12px; border-radius: 8px; margin-top: 12px;'>
                <p style='color: #00FFFF; font-weight: 600; margin: 0;'>
                    ✅ Selected: <span style='color: #00FF00; font-size: 18px;'>{days} Days</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

        # RIGHT COLUMN: REFRESH AND STATUS
        with col_right:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 20px; border-radius: 10px; border-left: 4px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 16px; margin-bottom: 12px;'>🔄 DATA REFRESH</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_refresh1, col_refresh2 = st.columns([1, 1])
            
            with col_refresh1:
                if st.button("🔄 Refresh Now", use_container_width=True, key="refresh_btn"):
                    fetch_binance_data.clear()
                    st.rerun()
            
            with col_refresh2:
                st.markdown("""
                <div style='text-align: center; padding: 10px;'>
                    <p style='color: #66FF99; font-size: 12px; margin: 0;'>Auto-refresh every 60s</p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 2: FETCH DATA
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">📥 Fetching Live Data</p>',
            unsafe_allow_html=True
        )

        with st.spinner("⏳ Connecting to Binance API..."):
            final_df = fetch_binance_data(st.session_state.selected_days)

        if final_df.empty:
            st.error("⚠️ Binance API unavailable - Please try again later")
            st.stop()

        os.makedirs("data", exist_ok=True)
        file_path = "data/binance_crypto_prices.csv"
        final_df.to_csv(file_path, index=False)

        st.markdown("""
        <div style='background: rgba(50, 255, 100, 0.15); padding: 15px; border-radius: 10px; border-left: 4px solid #33FF66;'>
            <p style='color: #66FF99; font-weight: 600; margin: 0;'>✅ Data Updated Successfully!</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 3: DATA PREVIEW & STATS (TWO COLUMNS)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">📋 Data Summary</p>',
            unsafe_allow_html=True
        )

        col_stats1, col_stats2 = st.columns([1, 1], gap="large")

        # LEFT COLUMN: STATISTICS
        with col_stats1:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 15px; border-radius: 10px; border-top: 3px solid #00FFFF;'>
            """, unsafe_allow_html=True)
            
            total_records = len(final_df)
            unique_cryptos = final_df["crypto"].nunique()
            date_range_str = f"{final_df['date'].min().strftime('%Y-%m-%d')} to {final_df['date'].max().strftime('%Y-%m-%d')}"
            
            st.metric(
                "📊 Total Records",
                f"{total_records:,}",
                delta=None
            )
            
            st.metric(
                "🪙 Cryptocurrencies",
                f"{unique_cryptos}",
                delta=None
            )
            
            st.markdown(f"""
            <p style='color: #00FFFF; font-weight: 600; font-size: 12px;'>
                📅 <span style='color: #FFD700;'>{date_range_str}</span>
            </p>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        # RIGHT COLUMN: CRYPTOS LIST
        with col_stats2:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 15px; border-radius: 10px; border-top: 3px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 14px; margin-bottom: 10px;'>💰 Tracked Cryptos</p>
            """, unsafe_allow_html=True)
            
            cryptos_list = final_df["crypto"].unique()
            crypto_names = {
                "BTCUSDT": "₿ Bitcoin",
                "ETHUSDT": "Ξ Ethereum",
                "SOLUSDT": "◎ Solana",
                "ADAUSDT": "₳ Cardano",
                "DOGEUSDT": "Ð Dogecoin"
            }
            
            crypto_display = "\n".join([
                f"<span style='color: #00FF00; font-weight: 600;'>✓</span> {crypto_names.get(c, c)}"
                for c in cryptos_list
            ])
            
            st.markdown(f"""
            <p style='color: #66FF99; font-size: 13px; line-height: 1.8; margin: 0;'>
                {crypto_display}
            </p>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 4: DATA TABLE & CHART (TWO COLUMNS)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">📊 Live Data Snapshot</p>',
            unsafe_allow_html=True
        )

        col_table, col_chart = st.columns([1, 1], gap="large")

        # LEFT COLUMN: RECENT DATA TABLE
        with col_table:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 10px; border-radius: 10px; border-left: 4px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 10px 0;'>📋 Last 10 Records</p>
            """, unsafe_allow_html=True)
            
            table_df = final_df.tail(10)[["date", "crypto", "price"]].copy()
            table_df["date"] = table_df["date"].dt.strftime("%Y-%m-%d")
            table_df["price"] = table_df["price"].astype(float).apply(lambda x: f"${x:.2f}")
            table_df.columns = ["📅 Date", "🪙 Crypto", "💵 Price"]
            
            st.dataframe(table_df, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # RIGHT COLUMN: SELECTION & CHART
        with col_chart:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 10px; border-radius: 10px; border-left: 4px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 13px; margin: 0 0 10px 0;'>📈 Price Trend</p>
            """, unsafe_allow_html=True)
            
            selected_coin = st.selectbox(
                "🔍 Select Cryptocurrency",
                final_df["crypto"].unique(),
                index=0,
                label_visibility="collapsed"
            )
            
            filtered = final_df[final_df["crypto"] == selected_coin]
            st.line_chart(
                filtered.set_index("date")["price"],
                use_container_width=True,
                height=250
            )
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 5: VOLATILITY & RISK ANALYSIS (TWO COLUMNS)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">⚠️ Risk Analysis</p>',
            unsafe_allow_html=True
        )

        col_vol, col_risk = st.columns([1, 1], gap="large")

        vol = calculate_volatility_simple(filtered)
        risk = risk_level(vol)

        # LEFT COLUMN: VOLATILITY
        with col_vol:
            st.markdown(f"""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 25px; border-radius: 12px; border-left: 4px solid #00FF00; text-align: center;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 14px; margin: 0 0 15px 0;'>📊 ANNUALIZED VOLATILITY</p>
                <p style='color: #00FF00; font-weight: bold; font-size: 42px; margin: 0;'>{vol:.2f}%</p>
                <p style='color: #66FF99; font-size: 12px; margin: 10px 0 0 0;'>Standard Deviation (Annualized)</p>
            </div>
            """, unsafe_allow_html=True)

        # RIGHT COLUMN: RISK LEVEL
        with col_risk:
            risk_color = "#33FF66" if "Low" in risk else ("#FFCC00" if "Medium" in risk else "#FF3333")
            
            st.markdown(f"""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 25px; border-radius: 12px; border-left: 4px solid {risk_color}; text-align: center;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 14px; margin: 0 0 15px 0;'>⚠️ RISK LEVEL</p>
                <p style='color: {risk_color}; font-weight: bold; font-size: 36px; margin: 0;'>{risk}</p>
                <p style='color: #66FF99; font-size: 12px; margin: 10px 0 0 0;'>Based on Volatility Threshold</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 6: DETAILED CRYPTO ANALYSIS (TWO COLUMNS)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">🔍 Individual Cryptocurrency Metrics</p>',
            unsafe_allow_html=True
        )

        col_crypto1, col_crypto2 = st.columns([1, 1], gap="large")

        crypto_list = final_df["crypto"].unique()

        # LEFT COLUMN: First set of cryptos
        with col_crypto1:
            for crypto in crypto_list[:3]:
                crypto_data = final_df[final_df["crypto"] == crypto]
                crypto_vol = calculate_volatility_simple(crypto_data)
                crypto_risk = risk_level(crypto_vol)
                risk_color = "#33FF66" if "Low" in crypto_risk else ("#FFCC00" if "Medium" in crypto_risk else "#FF3333")
                
                crypto_name = {
                    "BTCUSDT": "₿ Bitcoin",
                    "ETHUSDT": "Ξ Ethereum",
                    "SOLUSDT": "◎ Solana",
                    "ADAUSDT": "₳ Cardano",
                    "DOGEUSDT": "Ð Dogecoin"
                }.get(crypto, crypto)
                
                st.markdown(f"""
                <div style='background: rgba(15, 20, 45, 0.8); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {risk_color};'>
                    <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 8px 0;'>{crypto_name}</p>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='color: #FFD700; font-weight: 600;'>📊 Vol: <span style='color: #00FF00;'>{crypto_vol:.2f}%</span></span>
                        <span style='color: {risk_color}; font-weight: 600;'>{crypto_risk}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # RIGHT COLUMN: Remaining cryptos
        with col_crypto2:
            for crypto in crypto_list[3:]:
                crypto_data = final_df[final_df["crypto"] == crypto]
                crypto_vol = calculate_volatility_simple(crypto_data)
                crypto_risk = risk_level(crypto_vol)
                risk_color = "#33FF66" if "Low" in crypto_risk else ("#FFCC00" if "Medium" in crypto_risk else "#FF3333")
                
                crypto_name = {
                    "BTCUSDT": "₿ Bitcoin",
                    "ETHUSDT": "Ξ Ethereum",
                    "SOLUSDT": "◎ Solana",
                    "ADAUSDT": "₳ Cardano",
                    "DOGEUSDT": "Ð Dogecoin"
                }.get(crypto, crypto)
                
                st.markdown(f"""
                <div style='background: rgba(15, 20, 45, 0.8); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {risk_color};'>
                    <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 8px 0;'>{crypto_name}</p>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='color: #FFD700; font-weight: 600;'>📊 Vol: <span style='color: #00FF00;'>{crypto_vol:.2f}%</span></span>
                        <span style='color: {risk_color}; font-weight: 600;'>{crypto_risk}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 7: NAVIGATION
        # =====================================================
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

        with col_nav1:
            if st.button("⬅️ Dashboard", use_container_width=True):
                st.session_state.active_page = "dashboard"
                st.rerun()

        with col_nav2:
            st.markdown("""
            <div style='text-align: center; padding: 10px;'>
                <p style='color: #00FFFF; font-weight: 600; font-size: 12px; margin: 0;'>
                    ✅ Data Acquisition Complete | Ready for Milestone-2
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_nav3:
            if st.button("→ Next →", use_container_width=True):
                st.session_state.active_page = "milestone_2"
                st.rerun()

    # =====================================================
    # ⭐ MILESTONE 2: DATA PROCESSING & ANALYSIS (IMPROVED UI)
    # =====================================================
    elif st.session_state.active_page == "milestone_2":

        st.markdown(
            '<div class="header"><h2>📈 Milestone-2: Data Processing & Analysis</h2></div>',
            unsafe_allow_html=True
        )

        # =====================================================
        # SECTION 1: HEADER WITH CONTROLS
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">⚙️ Data Analysis Configuration</p>',
            unsafe_allow_html=True
        )

        col_info, col_refresh = st.columns([2, 1])

        with col_info:
            st.markdown(f"""
            <div style='background: rgba(0, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 14px; margin: 0;'>
                    📅 Time Period: <span style='color: #00FF00; font-size: 16px;'>{st.session_state.selected_days} Days</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_refresh:
            if st.button("🔄 Refresh Metrics", use_container_width=True, key="refresh_m2"):
                fetch_binance_data.clear()
                st.rerun()

        st.divider()

        # =====================================================
        # SECTION 2: LOAD DATA AND COMPUTE METRICS
        # =====================================================
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

        st.success("✅ Metrics computed successfully!", icon="✅")

        st.divider()

        # =====================================================
        # SECTION 3: METRICS TABLE (LEFT) & KEY STATS (RIGHT)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">📊 Risk Metrics Overview</p>',
            unsafe_allow_html=True
        )

        col_left_table, col_right_stats = st.columns([1.2, 1], gap="large")

        # LEFT COLUMN: RISK METRICS TABLE (COMPACT)
        with col_left_table:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-top: 3px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>📋 Risk Metrics Table</p>
            """, unsafe_allow_html=True)

            # Create styled dataframe
            metrics_display = metrics_df.copy()
            metrics_display["Volatility (%)"] = metrics_display["Volatility (%)"].apply(lambda x: f"<b style='color: #FFD700;'>{x:.2f}%</b>")
            metrics_display["Sharpe Ratio"] = metrics_display["Sharpe Ratio"].apply(lambda x: f"<b style='color: #00FF00;'>{x:.2f}</b>")
            metrics_display["Beta vs BTC"] = metrics_display["Beta vs BTC"].apply(lambda x: f"<b style='color: #66FF99;'>{x:.2f}</b>")

            # Display table with smaller font
            st.markdown("""
            <style>
            .metrics-table {
                font-size: 11px !important;
                line-height: 1.4 !important;
            }
            .metrics-table th {
                background-color: #00FFFF !important;
                color: black !important;
                font-weight: 700 !important;
                padding: 8px 4px !important;
                text-align: center !important;
            }
            .metrics-table td {
                padding: 6px 4px !important;
                text-align: center !important;
                border-bottom: 1px solid rgba(0, 255, 255, 0.2) !important;
            }
            .metrics-table tr:hover {
                background-color: rgba(0, 255, 255, 0.1) !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # Display metrics table
            st.dataframe(
                metrics_display,
                use_container_width=True,
                hide_index=True,
                height=250
            )

            st.markdown("</div>", unsafe_allow_html=True)

        # RIGHT COLUMN: KEY STATISTICS (HIGHLIGHTED)
        with col_right_stats:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-top: 3px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>🎯 Key Statistics</p>
            """, unsafe_allow_html=True)

            most_volatile = metrics_df.loc[metrics_df["Volatility (%)"].idxmax()]
            best_sharpe = metrics_df.loc[metrics_df["Sharpe Ratio"].idxmax()]
            lowest_beta = metrics_df.loc[metrics_df["Beta vs BTC"].idxmin()]

            st.markdown(f"""
            <div style='background: rgba(255, 215, 0, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 11px; margin: 0 0 4px 0;'>🔥 Most Volatile</p>
                <p style='color: #FFFF00; font-weight: 700; font-size: 14px; margin: 0;'>{most_volatile['Crypto']}</p>
                <p style='color: #FFD700; font-size: 10px; margin: 3px 0 0 0;'>{most_volatile['Volatility (%)']:.2f}% volatility</p>
            </div>

            <div style='background: rgba(51, 255, 102, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #33FF66;'>
                <p style='color: #33FF66; font-weight: 700; font-size: 11px; margin: 0 0 4px 0;'>🏆 Best Sharpe Ratio</p>
                <p style='color: #00FF00; font-weight: 700; font-size: 14px; margin: 0;'>{best_sharpe['Crypto']}</p>
                <p style='color: #66FF99; font-size: 10px; margin: 3px 0 0 0;'>{best_sharpe['Sharpe Ratio']:.2f} ratio</p>
            </div>

            <div style='background: rgba(100, 150, 255, 0.1); padding: 10px; border-radius: 8px; border-left: 4px solid #74C0FC;'>
                <p style='color: #74C0FC; font-weight: 700; font-size: 11px; margin: 0 0 4px 0;'>📉 Lowest Beta</p>
                <p style='color: #88DDFF; font-weight: 700; font-size: 14px; margin: 0;'>{lowest_beta['Crypto']}</p>
                <p style='color: #74C0FC; font-size: 10px; margin: 3px 0 0 0;'>{lowest_beta['Beta vs BTC']:.2f} vs BTC</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 4: VOLATILITY COMPARISON & ROLLING VOL (LEFT-RIGHT)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">📊 Volatility Analysis</p>',
            unsafe_allow_html=True
        )

        col_chart_left, col_chart_right = st.columns([1, 1], gap="large")

        # LEFT COLUMN: VOLATILITY COMPARISON BAR CHART (COMPACT)
        with col_chart_left:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 10px; border-radius: 10px; border-top: 3px solid #FF6B6B;'>
                <p style='color: #FF6B6B; font-weight: 700; font-size: 12px; margin: 0 0 10px 0;'>📉 Volatility Comparison</p>
            """, unsafe_allow_html=True)

            fig_bar = px.bar(
                metrics_df,
                x="Crypto",
                y="Volatility (%)",
                color="Volatility (%)",
                color_continuous_scale=[[0, "#33FF66"], [0.5, "#FFCC00"], [1, "#FF3333"]],
                title="",
                labels={"Volatility (%)": "Volatility (%)", "Crypto": ""}
            )

            fig_bar.update_layout(
                plot_bgcolor="rgba(15, 20, 45, 0.3)",
                paper_bgcolor="rgba(15, 20, 45, 0)",
                font=dict(color="#00FFFF", size=10),
                height=280,
                margin=dict(l=40, r=20, t=20, b=40),
                coloraxis_colorbar=dict(thickness=15, len=0.5, x=1.02),
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(0, 255, 255, 0.1)")
            )

            fig_bar.update_traces(
                marker=dict(line=dict(color="#00FFFF", width=1.5)),
                hovertemplate="<b>%{x}</b><br>Volatility: <b>%{y:.2f}%</b><extra></extra>"
            )

            st.plotly_chart(fig_bar, use_container_width=True, key="vol_comp")

            st.markdown("</div>", unsafe_allow_html=True)

        # RIGHT COLUMN: ROLLING VOLATILITY (COMPACT)
        with col_chart_right:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.8); padding: 10px; border-radius: 10px; border-top: 3px solid #74C0FC;'>
                <p style='color: #74C0FC; font-weight: 700; font-size: 12px; margin: 0 0 10px 0;'>📈 30-Day Rolling Volatility</p>
            """, unsafe_allow_html=True)

            selected_crypto = st.selectbox(
                "Select Cryptocurrency:",
                returns_df["crypto"].unique(),
                key="crypto_rolling",
                label_visibility="collapsed"
            )

            temp = returns_df[returns_df["crypto"] == selected_crypto].sort_values("date")

            fig_roll = px.line(
                temp,
                x="date",
                y="rolling_vol_30",
                title="",
                labels={"rolling_vol_30": "Volatility (%)", "date": "Date"}
            )

            fig_roll.update_layout(
                plot_bgcolor="rgba(15, 20, 45, 0.3)",
                paper_bgcolor="rgba(15, 20, 45, 0)",
                font=dict(color="#00FFFF", size=10),
                height=280,
                margin=dict(l=40, r=20, t=20, b=40),
                hovermode="x unified",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(0, 255, 255, 0.1)"),
                showlegend=False
            )

            fig_roll.update_traces(
                line=dict(color="#74C0FC", width=2.5),
                fill="tozeroy",
                fillcolor="rgba(116, 192, 252, 0.15)",
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Volatility: <b>%{y:.2f}%</b><extra></extra>"
            )

            st.plotly_chart(fig_roll, use_container_width=True, key="roll_vol")

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 5: DETAILED METRICS BREAKDOWN (TWO COLUMNS)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">🔍 Detailed Metrics Breakdown</p>',
            unsafe_allow_html=True
        )

        col_metrics_1, col_metrics_2 = st.columns([1, 1], gap="large")

        with col_metrics_1:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-left: 4px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 12px; margin: 0 0 12px 0;'>📊 Volatility Metrics</p>
            """, unsafe_allow_html=True)

            vol_stats = metrics_df["Volatility (%)"]
            
            st.markdown(f"""
            <div style='background: rgba(0, 255, 255, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px;'>
                <p style='color: #00FFFF; font-weight: 600; font-size: 11px; margin: 0;'>Average Volatility</p>
                <p style='color: #00FF00; font-weight: 700; font-size: 16px; margin: 4px 0 0 0;'>{vol_stats.mean():.2f}%</p>
            </div>

            <div style='background: rgba(255, 215, 0, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px;'>
                <p style='color: #FFD700; font-weight: 600; font-size: 11px; margin: 0;'>Max Volatility</p>
                <p style='color: #FFFF00; font-weight: 700; font-size: 16px; margin: 4px 0 0 0;'>{vol_stats.max():.2f}%</p>
            </div>

            <div style='background: rgba(51, 255, 102, 0.05); padding: 10px; border-radius: 8px;'>
                <p style='color: #33FF66; font-weight: 600; font-size: 11px; margin: 0;'>Min Volatility</p>
                <p style='color: #66FF99; font-weight: 700; font-size: 16px; margin: 4px 0 0 0;'>{vol_stats.min():.2f}%</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_metrics_2:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-left: 4px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 12px; margin: 0 0 12px 0;'>⚖️ Sharpe Ratio Metrics</p>
            """, unsafe_allow_html=True)

            sharpe_stats = metrics_df["Sharpe Ratio"]
            
            st.markdown(f"""
            <div style='background: rgba(255, 215, 0, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px;'>
                <p style='color: #FFD700; font-weight: 600; font-size: 11px; margin: 0;'>Average Sharpe</p>
                <p style='color: #FFFF00; font-weight: 700; font-size: 16px; margin: 4px 0 0 0;'>{sharpe_stats.mean():.2f}</p>
            </div>

            <div style='background: rgba(51, 255, 102, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px;'>
                <p style='color: #33FF66; font-weight: 600; font-size: 11px; margin: 0;'>Best Sharpe</p>
                <p style='color: #66FF99; font-weight: 700; font-size: 16px; margin: 4px 0 0 0;'>{sharpe_stats.max():.2f}</p>
            </div>

            <div style='background: rgba(116, 192, 252, 0.05); padding: 10px; border-radius: 8px;'>
                <p style='color: #74C0FC; font-weight: 600; font-size: 11px; margin: 0;'>Worst Sharpe</p>
                <p style='color: #88DDFF; font-weight: 700; font-size: 16px; margin: 4px 0 0 0;'>{sharpe_stats.min():.2f}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 6: BETA ANALYSIS (THREE COLUMNS)
        # =====================================================
        st.markdown(
            '<p class="milestone-subheader">🔗 Beta Analysis (vs Bitcoin)</p>',
            unsafe_allow_html=True
        )

        beta_stats = metrics_df["Beta vs BTC"]
        col_beta_1, col_beta_2, col_beta_3 = st.columns([1, 1, 1], gap="medium")

        with col_beta_1:
            st.markdown(f"""
            <div style='background: rgba(116, 192, 252, 0.15); padding: 15px; border-radius: 10px; text-align: center; border-left: 4px solid #74C0FC;'>
                <p style='color: #74C0FC; font-weight: 600; font-size: 11px; margin: 0;'>📊 Average Beta</p>
                <p style='color: #88DDFF; font-weight: 700; font-size: 18px; margin: 8px 0 0 0;'>{beta_stats.mean():.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_beta_2:
            st.markdown(f"""
            <div style='background: rgba(51, 255, 102, 0.15); padding: 15px; border-radius: 10px; text-align: center; border-left: 4px solid #33FF66;'>
                <p style='color: #33FF66; font-weight: 600; font-size: 11px; margin: 0;'>📈 Highest Beta</p>
                <p style='color: #66FF99; font-weight: 700; font-size: 18px; margin: 8px 0 0 0;'>{beta_stats.max():.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_beta_3:
            st.markdown(f"""
            <div style='background: rgba(255, 107, 107, 0.15); padding: 15px; border-radius: 10px; text-align: center; border-left: 4px solid #FF6B6B;'>
                <p style='color: #FF6B6B; font-weight: 600; font-size: 11px; margin: 0;'>📉 Lowest Beta</p>
                <p style='color: #FF9999; font-weight: 700; font-size: 18px; margin: 8px 0 0 0;'>{beta_stats.min():.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # =====================================================
        # SECTION 7: NAVIGATION
        # =====================================================
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

        with col_nav1:
            if st.button("⬅️ Back", use_container_width=True, key="nav_back_m2"):
                st.session_state.active_page = "milestone_1"
                st.rerun()

        with col_nav2:
            st.markdown("""
            <div style='text-align: center; padding: 12px; background: rgba(0, 255, 255, 0.1); border-radius: 8px;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 12px; margin: 0;'>
                    ✅ Data Processing Complete | Ready for Milestone-3
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_nav3:
            if st.button("→ Next →", use_container_width=True, key="nav_next_m2"):
                st.session_state.active_page = "milestone_3"
                st.rerun()

    # =====================================================
    # ⭐ MILESTONE 3: TIME-SERIES & VISUALIZATION (REVAMPED UI)
    # =====================================================
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

            if not os.path.exists(raw_path):
                return pd.DataFrame()

            df = pd.read_csv(raw_path)
            df = df.rename(columns={"date": "Date", "price": "Close", "crypto": "Crypto"})
            df["Date"] = pd.to_datetime(df["Date"]) 
            df = df.sort_values(["Crypto", "Date"]).reset_index(drop=True)
            df["Close"] = df["Close"].astype(float)
            df["Returns"] = df.groupby("Crypto")["Close"].transform(lambda x: x.pct_change())
            window = 30
            df["Volatility"] = df.groupby("Crypto")["Returns"].transform(
                lambda x: x.rolling(window).std() * np.sqrt(TRADING_DAYS)
            )
            df["Sharpe_Ratio"] = df.groupby("Crypto")["Returns"].transform(
                lambda x: (x.rolling(window).mean() * TRADING_DAYS) / (x.rolling(window).std() * np.sqrt(TRADING_DAYS))
            )

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

        min_date = proc_df["Date"].min().date()
        max_date = proc_df["Date"].max().date()

        c1, c2 = st.columns([2, 3])
        with c1:
            date_range = st.date_input("Select date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            cryptos = st.multiselect("Select cryptocurrencies", options=proc_df["Crypto"].unique(), default=list(proc_df["Crypto"].unique()))

        with c2:
            st.markdown("\n")
            if st.button("🔄 Refresh Processed Data", use_container_width=True):
                try:
                    if os.path.exists("data/crypto_processed.csv"):
                        os.remove("data/crypto_processed.csv")
                except Exception:
                    pass
                proc_df = load_or_build_processed()
                st.rerun()

        start, end = date_range
        mask = (proc_df["Date"].dt.date >= start) & (proc_df["Date"].dt.date <= end) & (proc_df["Crypto"].isin(cryptos))
        filtered = proc_df.loc[mask].copy()

        if filtered.empty:
            st.warning("No data for selected filters")
        else:
            # --- UI: Two columns, Price Trend & Volatility Trend ---
            st.markdown('<p class="milestone-subheader">📈 <b>Price & Volatility Trends</b></p>', unsafe_allow_html=True)
            col_left, col_right = st.columns(2)

            # Price Trend (Left, Small)
            with col_left:
                st.markdown('<div style="font-weight:bold; color:#00FFFF; font-size:16px; margin-bottom:8px;">💰 Price Trend</div>', unsafe_allow_html=True)
                fig_price = px.line(filtered, x="Date", y="Close", color="Crypto", title="")
                fig_price.update_layout(
                    plot_bgcolor="rgba(15, 20, 45, 0.5)", 
                    paper_bgcolor="rgba(15, 20, 45, 0.1)", 
                    height=270,  # Smaller height
                    showlegend=True,
                    margin=dict(l=20, r=15, t=30, b=20),
                    font=dict(color="#00FFFF", size=12)
                )
                st.plotly_chart(fig_price, use_container_width=True)

            # Volatility Trend (Right, Small)
            with col_right:
                st.markdown('<div style="font-weight:bold; color:#FF6B6B; font-size:16px; margin-bottom:8px;">📊 Volatility Trend</div>', unsafe_allow_html=True)
                fig_vol = px.line(filtered, x="Date", y="Volatility", color="Crypto", title="")
                fig_vol.update_layout(
                    plot_bgcolor="rgba(15, 20, 45, 0.5)", 
                    paper_bgcolor="rgba(15, 20, 45, 0.1)", 
                    height=270,
                    showlegend=True,
                    margin=dict(l=20, r=15, t=30, b=20),
                    font=dict(color="#FF6B6B", size=12)
                )
                st.plotly_chart(fig_vol, use_container_width=True)

            # --- UI: Two columns, Risk Return Scatter & KPIs ---
            st.markdown('<p class="milestone-subheader">⚖️ <b>Risk–Return & KPIs</b></p>', unsafe_allow_html=True)
            col_left2, col_right2 = st.columns(2)

            # Risk-Return Scatter (Left)
            with col_left2:
                st.markdown('<div style="font-weight:bold; color:#FFD700; font-size:16px; margin-bottom:8px;">📈 Risk–Return Scatter Plot</div>', unsafe_allow_html=True)
                grp = filtered.groupby("Crypto").agg(
                    Average_Return=("Returns", lambda x: x.mean() * TRADING_DAYS * 100),
                    Average_Volatility=("Volatility", "mean"),
                    Avg_Sharpe=("Sharpe_Ratio", "mean")
                ).reset_index()
                fig_scatter = px.scatter(
                    grp, x="Average_Volatility", y="Average_Return", color="Crypto",
                    size_max=40, hover_data=["Avg_Sharpe"], title=""
                )
                fig_scatter.update_layout(
                    plot_bgcolor="rgba(15, 20, 45, 0.5)", 
                    paper_bgcolor="rgba(15, 20, 45, 0.1)",
                    height=270,
                    margin=dict(l=20, r=15, t=30, b=20),
                    font=dict(color="#FFD700", size=12),
                    xaxis_title="Volatility (%)",
                    yaxis_title="Annualized Return (%)"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

            # KPIs Card Table (Right)
            with col_right2:
                st.markdown('<div style="font-weight:bold; color:#33FF66; font-size:16px; margin-bottom:8px;">🎯 KPIs By Asset</div>', unsafe_allow_html=True)
                kpi_grp = filtered.groupby("Crypto").agg(
                    Volatility=("Volatility", "mean"),
                    Return=("Returns", lambda x: x.mean() * TRADING_DAYS * 100),
                    Sharpe=("Sharpe_Ratio", "mean")
                ).round(2).reset_index()

                # Show as a visually separated KPI card per asset.
                for _, row in kpi_grp.iterrows():
                    st.markdown(
                        f"""
                        <div style="background:rgba(51,255,102,0.08);border-radius:8px;padding:10px;margin-bottom:12px;border-left:4px solid #00FF00;">
                            <span style="font-weight:800;color:#00FFFF;font-size:15px;">{row['Crypto']}</span>
                            <div style="margin-top:8px;">
                                <span style="color:#FFD700;font-weight:bold;font-size:13px;">Volatility: </span>
                                <span style="font-size:13px;color:#FFD700;font-weight:bold;">{row['Volatility']:.2f}%</span><br>
                                <span style="color:#00FF00;font-weight:bold;font-size:13px;">Return: </span>
                                <span style="font-size:13px;color:#00FF00;font-weight:bold;">{row['Return']:.2f}%</span><br>
                                <span style="color:#74C0FC;font-weight:bold;font-size:13px;">Sharpe: </span>
                                <span style="font-size:13px;color:#74C0FC;font-weight:bold;">{row['Sharpe']:.2f}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.divider()

        # --- Navigation Buttons ---
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        
        with col_nav1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.active_page = "milestone_2"
                st.rerun()

        with col_nav2:
            st.markdown("""
            <div style='text-align: center; padding: 10px;'>
                <p style='color: #00FFFF; font-weight: 600; font-size: 12px; margin: 0;'>
                    ✅ Visualization Complete | Ready for Milestone-4
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_nav3:
            if st.button("Next →", use_container_width=True):
                st.session_state.active_page = "milestone_4"
                st.rerun()

    # =====================================================
    # ⭐ MILESTONE 4: RISK CLASSIFICATION & REPORTING (IMPROVED UI)
    # =====================================================
    elif st.session_state.active_page == "milestone_4":

        st.markdown(
            '<div class="header"><h2>📋 Milestone-4: Risk Classification & Reporting</h2></div>',
            unsafe_allow_html=True
        )

        file_path = "data/binance_crypto_prices.csv"

        if not os.path.exists(file_path):
            st.error("⚠️ Run Milestone-1 first to acquire data.")
            if st.button("⬅️ Back to Dashboard", use_container_width=True):
                st.session_state.active_page = "dashboard"
                st.rerun()
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

        st.markdown(
            '<p class="milestone-subheader">⚙️ Risk Threshold Configuration</p>',
            unsafe_allow_html=True
        )

        col_thresh1, col_thresh2 = st.columns(2)

        with col_thresh1:
            low_threshold = st.slider(
                "🟢 Low Risk (%)",
                min_value=5,
                max_value=30,
                value=st.session_state.risk_thresholds["low"],
                step=1
            )
            st.session_state.risk_thresholds["low"] = low_threshold

        with col_thresh2:
            medium_threshold = st.slider(
                "🟡 Medium Risk (%)",
                min_value=30,
                max_value=100,
                value=st.session_state.risk_thresholds["medium"],
                step=1
            )
            st.session_state.risk_thresholds["medium"] = medium_threshold

        st.divider()

        st.markdown(
            '<p class="milestone-subheader">📊 Risk Classification Report</p>',
            unsafe_allow_html=True
        )

        risk_report = generate_risk_report_dataframe(returns_df, metrics_df)
        dashboard_data = create_risk_dashboard_data(price_df, metrics_df)

        # --- Left-Right Layout: Risk Distribution & Stats ---
        col_chart1, col_chart2 = st.columns(2, gap="large")

        with col_chart1:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-top: 3px solid #FF6B6B;'>
                <p style='color: #FF6B6B; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>📊 Risk Distribution</p>
            """, unsafe_allow_html=True)
            
            fig_dist = create_risk_distribution_chart(metrics_df)
            st.plotly_chart(fig_dist, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_chart2:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-top: 3px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>🎯 Asset Count by Risk</p>
            """, unsafe_allow_html=True)
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)

            with col_stat1:
                st.metric(
                    "🟢 Low",
                    dashboard_data["low_risk_count"],
                    delta=None
                )

            with col_stat2:
                st.metric(
                    "🟡 Medium",
                    dashboard_data["medium_risk_count"],
                    delta=None
                )

            with col_stat3:
                st.metric(
                    "🔴 High",
                    dashboard_data["high_risk_count"],
                    delta=None
                )
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # --- Left-Right Layout: Risk Overview & Gauge ---
        col_left_gauge, col_right_gauge = st.columns(2, gap="large")

        with col_left_gauge:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-top: 3px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>💡 Portfolio Insights</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: rgba(255, 215, 0, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 11px; margin: 0 0 4px 0;'>📈 Avg Volatility</p>
                <p style='color: #FFFF00; font-weight: 700; font-size: 16px; margin: 0;'>{dashboard_data['avg_volatility']:.2f}%</p>
            </div>

            <div style='background: rgba(51, 255, 102, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #33FF66;'>
                <p style='color: #33FF66; font-weight: 700; font-size: 11px; margin: 0 0 4px 0;'>📊 Avg Sharpe Ratio</p>
                <p style='color: #66FF99; font-weight: 700; font-size: 16px; margin: 0;'>{dashboard_data['avg_sharpe']:.2f}</p>
            </div>

            <div style='background: rgba(100, 150, 255, 0.1); padding: 10px; border-radius: 8px; border-left: 4px solid #74C0FC;'>
                <p style='color: #74C0FC; font-weight: 700; font-size: 11px; margin: 0 0 4px 0;'>🪙 Total Assets</p>
                <p style='color: #88DDFF; font-weight: 700; font-size: 16px; margin: 0;'>{dashboard_data['total_cryptos']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right_gauge:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-top: 3px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>⚖️ Overall Risk</p>
            """, unsafe_allow_html=True)
            
            fig_gauge = create_plotly_risk_gauge(
                "Overall",
                dashboard_data["avg_volatility"]
            )
            st.plotly_chart(fig_gauge, use_container_width=True, key="risk_gauge")
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.markdown(
            '<p class="milestone-subheader">📋 Detailed Risk Assessment</p>',
            unsafe_allow_html=True
        )

        display_report = risk_report.copy()
        st.dataframe(display_report, use_container_width=True, hide_index=True)

        st.divider()

        # --- High Risk Assets Alert ---
        high_risk_assets = metrics_df[metrics_df["Volatility (%)"] > st.session_state.risk_thresholds["medium"]]

        if not high_risk_assets.empty:
            st.markdown(
                '<p class="milestone-subheader">⚠️ High-Risk Assets Alert</p>',
                unsafe_allow_html=True
            )

            col_risk_alert1, col_risk_alert2 = st.columns(2, gap="large")
            
            for idx, (_, row) in enumerate(high_risk_assets.iterrows()):
                if idx % 2 == 0:
                    col = col_risk_alert1
                else:
                    col = col_risk_alert2
                    
                with col:
                    st.markdown(
                        f"""
                        <div class="risk-high" style="padding: 15px; border-radius: 10px; margin-bottom: 12px;">
                        <b style='font-size: 14px;'>🔴 {row['Crypto']}</b><br/>
                        <span style='font-size: 13px;'>Volatility: <b>{row['Volatility (%)']:.2f}%</b></span><br/>
                        <span style='font-size: 13px;'>Sharpe: <b>{row['Sharpe Ratio']:.2f}</b></span><br/>
                        <span style='font-size: 13px;'>Beta: <b>{row['Beta vs BTC']:.2f}</b></span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.divider()

        # --- Left-Right Layout: Key Insights ---
        st.markdown(
            '<p class="milestone-subheader">💡 Key Insights</p>',
            unsafe_allow_html=True
        )

        col_insights1, col_insights2 = st.columns(2, gap="large")

        with col_insights1:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 15px; border-radius: 10px; border-left: 4px solid #00FFFF;'>
                <p style='color: #00FFFF; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>📊 Portfolio Stats</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='font-size: 13px; line-height: 2; color: #66FF99;'>
                <b>Total Assets:</b> {dashboard_data['total_cryptos']}<br>
                <b>High Risk:</b> {dashboard_data['high_risk_count']}<br>
                <b>Medium Risk:</b> {dashboard_data['medium_risk_count']}<br>
                <b>Low Risk:</b> {dashboard_data['low_risk_count']}<br>
                <b>Avg Volatility:</b> {dashboard_data['avg_volatility']:.2f}%<br>
                <b>Avg Sharpe:</b> {dashboard_data['avg_sharpe']:.2f}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col_insights2:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 15px; border-radius: 10px; border-left: 4px solid #FFD700;'>
                <p style='color: #FFD700; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>🎯 Top Performers</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='font-size: 13px; line-height: 2; color: #FFDD66;'>
                <b>Most Volatile:</b><br>
                {dashboard_data['highest_vol_crypto']}<br>
                <span style='color: #FFD700;'>{dashboard_data['highest_vol_value']:.2f}%</span><br><br>
                <b>Best Risk-Adjusted:</b><br>
                {dashboard_data['best_sharpe_crypto']}<br>
                <span style='color: #00FF00;'>Sharpe: {dashboard_data['best_sharpe_value']:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # --- Export Reports ---
        st.markdown(
            '<p class="milestone-subheader">📥 Export Report</p>',
            unsafe_allow_html=True
        )

        col_export1, col_export2 = st.columns(2, gap="large")

        with col_export1:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-left: 4px solid #33FF66;'>
                <p style='color: #33FF66; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>📄 CSV Export</p>
            """, unsafe_allow_html=True)
            
            if st.button("📥 Generate CSV Report", use_container_width=True, key="csv_export"):
                csv_data = export_risk_report_csv(display_report)
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col_export2:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 12px; border-radius: 10px; border-left: 4px solid #74C0FC;'>
                <p style='color: #74C0FC; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>📕 PDF Export</p>
            """, unsafe_allow_html=True)
            
            if st.button("📥 Generate PDF Report", use_container_width=True, key="pdf_export"):
                with st.spinner("⏳ Generating PDF..."):
                    pdf_data = generate_risk_report_pdf(display_report, dashboard_data)
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_data,
                        file_name=f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # --- Risk Management Recommendations ---
        st.markdown(
            '<p class="milestone-subheader">📌 Risk Management Recommendations</p>',
            unsafe_allow_html=True
        )

        col_rec_left, col_rec_right = st.columns(2, gap="large")

        with col_rec_left:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 15px; border-radius: 10px; border-left: 4px solid #FF6B6B;'>
                <p style='color: #FF6B6B; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>⚠️ Action Items</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='font-size: 12px; line-height: 1.8; color: #FF9999;'>
            <b>1. Monitor High-Risk Positions</b><br>
            {dashboard_data['high_risk_count']} assets need close tracking<br><br>
            <b>2. Diversify Portfolio</b><br>
            Add {dashboard_data['low_risk_count']} low-volatility assets<br><br>
            <b>3. Set Stop-Loss Levels</b><br>
            Use 2x standard deviation thresholds<br><br>
            <b>4. Quarterly Rebalancing</b><br>
            Adjust portfolio allocations
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        with col_rec_right:
            st.markdown("""
            <div style='background: rgba(15, 20, 45, 0.9); padding: 15px; border-radius: 10px; border-left: 4px solid #00FF00;'>
                <p style='color: #00FF00; font-weight: 700; font-size: 13px; margin: 0 0 12px 0;'>✅ Current Thresholds</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='font-size: 12px; line-height: 1.8; color: #66FF99;'>
            <b>🟢 Low Risk:</b><br>
            &lt; {st.session_state.risk_thresholds['low']}%<br><br>
            <b>🟡 Medium Risk:</b><br>
            {st.session_state.risk_thresholds['low']}% - {st.session_state.risk_thresholds['medium']}%<br><br>
            <b>🔴 High Risk:</b><br>
            &gt; {st.session_state.risk_thresholds['medium']}%<br><br>
            <b>Generated:</b><br>
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # --- Navigation ---
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        
        with col_nav1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.active_page = "milestone_3"
                st.rerun()

        with col_nav2:
            st.markdown("""
            <div style='text-align: center; padding: 10px;'>
                <p style='color: #00FFFF; font-weight: 600; font-size: 12px; margin: 0;'>
                    ✅ All Milestones Complete!
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_nav3:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.active_page = "dashboard"
                st.rerun()
