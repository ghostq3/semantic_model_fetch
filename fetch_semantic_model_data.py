import streamlit as st
import requests
import pandas as pd

# ----------------------------
# 🔐 Secrets (from Streamlit)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]
RESOURCE = "https://analysis.windows.net/powerbi/api"

WORKSPACE_ID = "9755694b-649e-4a01-8386-eee2bd91079e"
DATASET_ID = "5b64ca41-91bd-4db4-b005-0c0327887b5e"

# -------------------------------------
# 🔑 Step 1. Get Access Token
# -------------------------------------
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# -------------------------------------
# 📊 Step 2. Run DAX Query on Dataset
# -------------------------------------
def run_dax_query(access_token, dax_query):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    body = {"queries": [{"query": dax_query}]}
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()

# -------------------------------------
# 🧠 Step 3. Convert DAX Result to DataFrame
# -------------------------------------
def dax_to_df(result_json):
    rows = result_json["results"][0]["tables"][0]["rows"]
    return pd.DataFrame(rows)

# -------------------------------------
# ⚙️ Step 4. Streamlit App
# -------------------------------------
st.set_page_config(page_title="AI KPI Dashboard", layout="wide")
st.title("📊 AI KPI Dashboard")

with st.spinner("Fetching Power BI data automatically..."):
    try:
        token = get_access_token()

        # ----------------------------
        # 🧮 Load Measures
        # ----------------------------
        dax_measures = """
        EVALUATE
        ROW(
            "Revenue", [Revenue],
            "Win Rate", [Win Rate],
            "Average Sales Cycle (Won)", [Average Sales Cycle (Won)],
            "AI Influenced Win Rate", [AI Influenced Win Rate],
            "Total Opportunities", [Total Opportunities],
            "Win More", Win More (Total Opportunities),
            "Won Opportunities", [Won Opps #],
            "Average Deal Size", [Average Deal Size],
            "AI Users", [AI Users],
            "AI Invocations", [AI Invocations]
        )
        """
        measures_result = run_dax_query(token, dax_measures)
        measures_df = dax_to_df(measures_result)

        st.success("✅ *Measures loaded successfully")
        st.dataframe(measures_df)

        # ----------------------------
        # 🔹 Top KPI Metrics
        # ----------------------------
        win_more = measures_df["Win More"].iloc[0] + 10 
        win_rate = measures_df["Win Rate"].iloc[0]
        avg_cycle = measures_df["Average Sales Cycle (Won)"].iloc[0]
        avg_deal_size = measures_df["Average Deal Size"].iloc[0]
        ai_win_rate = measures_df["AI Influenced Win Rate"].iloc[0]

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Win More", f"{win_more:.1f}%")
        col2.metric("Win Rate", f"{win_rate:.1f}%")
        col3.metric("Avg Sales Cycle", f"{avg_cycle} days")
        col4.metric("Avg Deal Size", f"${avg_deal_size:,.0f}")
        col5.metric("AI Influenced Win Rate", f"{ai_win_rate:.1f}%")

        st.markdown("---")

        # ----------------------------
        # 📌 Core AI & Sales Metrics (Color-Coded)
        # ----------------------------
        st.subheader("📌 Core AI & Sales Metrics")

        # CSS styling for metric cards
        st.markdown("""
            <style>
                .metric-card {
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    text-align: center;
                    transition: transform 0.2s ease;
                }
                .metric-card:hover { transform: scale(1.02); }
                .metric-label { font-size: 16px; color: #555; margin-bottom: 5px; }
                .metric-value { font-size: 28px; font-weight: 600; }
            </style>
        """, unsafe_allow_html=True)

        # Pull KPI values
        ai_usage = measures_df["AI Users"].iloc[0]
        sales = measures_df["Revenue"].iloc[0]
        growth = measures_df["AI Influenced Win Rate"].iloc[0]  # example, adjust if needed

        # Dynamic colors
        growth_color = "green" if growth >= 0 else "red"
        ai_color = "green" if ai_usage >= 50 else "orange"
        sales_color = "#0078D7"

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Current AI Usage %</div>"
                f"<div class='metric-value' style='color:{ai_color};'>{ai_usage:.1f}%</div></div>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Latest Monthly Sales</div>"
                f"<div class='metric-value' style='color:{sales_color};'>${sales:,.0f}</div></div>",
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>Sales Growth (MoM)</div>"
                f"<div class='metric-value' style='color:{growth_color};'>{growth:.2f}%</div></div>",
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
