import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ----------------------------
# 🔐 Secrets (from Streamlit)
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
@st.cache_data(show_spinner=False)
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE
    }
    res = requests.post(AUTH_URL, data=payload)
    res.raise_for_status()
    return res.json()["access_token"]

# ----------------------------
# 🧠 Run DAX Query
# ----------------------------
def run_dax_query(query, token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}
    res = requests.post(url, headers=headers, json=body)
    res.raise_for_status()
    return res.json()

# ----------------------------
# 📊 Streamlit Dashboard
# ----------------------------
st.set_page_config(page_title="AI Sales Dashboard", layout="wide")
st.title("🤖 AI Sales Performance Dashboard")

# Get access token
access_token = get_access_token()

# ----------------------------
# 📈 Load Data (Fact + Measures)
# ----------------------------
st.write("Fetching Power BI Data...")

# DAX Query to combine dim_date and measures
dax_query = """
EVALUATE
SELECTCOLUMNS(
    dim_date,
    "MonthYear", dim_date[MonthYear],
    "Revenue", [Revenue],
    "Win Rate", [Win Rate],
    "Average Sales Cycle (Won)", [Average Sales Cycle (Won)],
    "AI Influenced Win Rate", [AI Influenced Win Rate],
    "Won Opps #", [Won Opps #],
    "Average Deal Size", [Average Deal Size],
    "AI Users", [AI Users],
    "AI Invocations", [AI Invocations]
)
"""

try:
    result = run_dax_query(dax_query, access_token)
    table_data = result["results"][0]["tables"][0]["rows"]
    df = pd.DataFrame(table_data)
    df["MonthYear"] = pd.to_datetime(df["MonthYear"], errors="coerce")
    st.success("✅ Data fetched successfully!")
except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")
    st.stop()

# ----------------------------
# 🧍 Region Selector
# ----------------------------
region_query = "EVALUATE SUMMARIZE(fact_opportunity, fact_opportunity[RegionSelector])"
try:
    region_data = run_dax_query(region_query, access_token)
    regions = [r["fact_opportunity[RegionSelector]"] for r in region_data["results"][0]["tables"][0]["rows"]]
    selected_region = st.selectbox("🌎 Select Region", ["All"] + regions)
except:
    selected_region = "All"

# ----------------------------
# 📊 Layout
# ----------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Revenue", f"${df['Revenue'].sum():,.0f}")
col2.metric("🏆 Win Rate", f"{df['Win Rate'].mean():.2f}%")
col3.metric("🧠 AI Win Rate", f"{df['AI Influenced Win Rate'].mean():.2f}%")
col4.metric("⏱ Avg. Sales Cycle", f"{df['Average Sales Cycle (Won)'].mean():.1f} days")

st.markdown("---")

# ----------------------------
# 📈 Charts
# ----------------------------
st.subheader("📈 Sales Trend Over Time")
fig1 = px.line(df, x="MonthYear", y="Revenue", title="Revenue Trend Over Time", markers=True)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("⏱ Average Sales Cycle Trend")
fig2 = px.line(df, x="MonthYear", y="Average Sales Cycle (Won)", title="Average Sales Cycle (Won)", markers=True)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("💰 Win Rate by Region")
region_query = """
EVALUATE
SUMMARIZECOLUMNS(
    fact_opportunity[RegionSelector],
    "Win Rate", [Win Rate]
)
"""
try:
    region_res = run_dax_query(region_query, access_token)
    region_df = pd.DataFrame(region_res["results"][0]["tables"][0]["rows"])
    fig3 = px.bar(region_df, x="fact_opportunity[RegionSelector]", y="Win Rate", title="Win Rate by Region")
    st.plotly_chart(fig3, use_container_width=True)
except:
    st.warning("⚠️ Unable to fetch region breakdown.")

st.subheader("🧠 AI Influence vs Total Deals")
fig4 = px.scatter(
    df,
    x="Won Opps #",
    y="AI Influenced Win Rate",
    size="Average Deal Size",
    color="Revenue",
    title="AI Influence vs Total Deals",
)
st.plotly_chart(fig4, use_container_width=True)

# ----------------------------
# 🧍‍♂️ AI Cards
# ----------------------------
st.subheader("🧍‍♂️ AI Users & Invocations")
colA, colB = st.columns(2)
colA.metric("AI Users", f"{df['AI Users'].sum():,.0f}")
colB.metric("AI Invocations", f"{df['AI Invocations'].sum():,.0f}")
