import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ----------------------------
# 🔐 Secrets (Streamlit Cloud)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]

WORKSPACE_ID = "9755694b-649e-4a01-8386-eee2bd91079e"
DATASET_ID = "5b64ca41-91bd-4db4-b005-0c0327887b5e"

RESOURCE = "https://analysis.windows.net/powerbi/api"
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"

# ----------------------------
# ⚙️ Get Access Token
# ----------------------------
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE
    }
    response = requests.post(AUTH_URL, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

# ----------------------------
# 🧠 Run DAX Query
# ----------------------------
def run_dax_query(query, token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    result = response.json()
    tables = result.get("results", [])[0].get("tables", [])
    if tables:
        return pd.DataFrame(tables[0]["rows"])
    else:
        raise ValueError("No data returned")

# ----------------------------
# 🧩 DAX Query
# ----------------------------
DAX_QUERY = """
EVALUATE
SELECTCOLUMNS(
    fact_opportunity,
    "Region", fact_opportunity[RegionSelector],
    "MonthYear", RELATED(dim_date[MonthYear]),
    "Revenue", [Revenue],
    "Win Rate", [Win Rate],
    "Average Sales Cycle (Won)", [Average Sales Cycle (Won)],
    "AI Influenced Win Rate", [AI Influenced Win Rate],
    "Won Opps #", [Won Opps #],
    "Average Deal Size", [Average Deal Size],
    "AI Users", [AI Users],
    "AI Invocations", [AI Invocations]
)
ORDER BY RELATED(dim_date[MonthYear])
"""

# ----------------------------
# 🚀 Streamlit UI
# ----------------------------
st.set_page_config(page_title="AI Sales KPI Dashboard", layout="wide")
st.title("📊 AI Sales KPI Dashboard (Live from Power BI Semantic Model)")

if st.button("Fetch & Visualize Data"):
    try:
        access_token = get_access_token()
        st.success("✅ Access token acquired successfully!")

        df = run_dax_query(DAX_QUERY, access_token)
        st.success("✅ Data loaded successfully from semantic model!")

        # Clean and prepare data
        df = df.dropna(subset=["MonthYear"])
        df["MonthYear"] = pd.Categorical(df["MonthYear"], ordered=True)
        df = df.sort_values("MonthYear")

        # ----------------------------
        # 📈 KPI CARDS
        # ----------------------------
        latest = df.iloc[-1]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Revenue", f"${latest['Revenue']:,.0f}")
        col2.metric("Win Rate", f"{latest['Win Rate']:.1f}%")
        col3.metric("Avg Sales Cycle", f"{latest['Average Sales Cycle (Won)']:.0f} days")
        col4.metric("AI Win Rate", f"{latest['AI Influenced Win Rate']:.1f}%")
        col5.metric("Avg Deal Size", f"${latest['Average Deal Size']:,.0f}")

        # AI Users & Invocations
        st.subheader("🧍‍♂️ AI Usage Metrics")
        col1, col2 = st.columns(2)
        col1.metric("AI Users", f"{latest['AI Users']:,.0f}")
        col2.metric("AI Invocations", f"{latest['AI Invocations']:,.0f}")

        # ----------------------------
        # 📊 SALES TREND
        # ----------------------------
        st.subheader("📈 Sales Trend Over Time")
        fig_sales = px.line(
            df, x="MonthYear", y="Revenue", color="Region",
            title="Revenue Trend by Region",
            markers=True
        )
        st.plotly_chart(fig_sales, use_container_width=True)

        # ----------------------------
        # 💰 WIN RATE BY REGION
        # ----------------------------
        st.subheader("💰 Win Rate by Region")
        latest_win = df.groupby("Region", as_index=False)["Win Rate"].mean()
        fig_win = px.bar(
            latest_win, x="Region", y="Win Rate", text_auto=".1f",
            title="Average Win Rate by Region"
        )
        st.plotly_chart(fig_win, use_container_width=True)

        # ----------------------------
        # 🧠 AI INFLUENCE vs TOTAL DEALS
        # ----------------------------
        st.subheader("🧠 AI Influence vs Total Deals")
        fig_ai = px.scatter(
            df, x="AI Influenced Win Rate", y="Won Opps #", color="Region",
            size="Revenue", hover_data=["Average Deal Size"],
            title="AI Influence vs. Total Opportunities"
        )
        st.plotly_chart(fig_ai, use_container_width=True)

        # ----------------------------
        # ⏱️ AVERAGE SALES CYCLE TREND
        # ----------------------------
        st.subheader("⏱️ Average Sales Cycle Trend")
        fig_cycle = px.line(
            df, x="MonthYear", y="Average Sales Cycle (Won)", color="Region",
            title="Average Sales Cycle (Won) Over Time", markers=True
        )
        st.plotly_chart(fig_cycle, use_container_width=True)

        # ----------------------------
        # 📋 RAW DATA
        # ----------------------------
        st.subheader("📋 Raw Data Preview")
        st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
