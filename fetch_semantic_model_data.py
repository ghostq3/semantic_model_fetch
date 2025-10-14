import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ----------------------------
# 🔐 Secrets
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
# ⚙️ Step 4. Fetch Data & Measures
# -------------------------------------
st.title("🔗 Power BI Semantic Model – Streamlit Visuals")

with st.spinner("Fetching Power BI data automatically..."):
    try:
        token = get_access_token()

        # ----- dim_date -----
        dax_date = """
        EVALUATE
        SELECTCOLUMNS(
            dim_date,
            "MonthYear", dim_date[MonthYear],
            "MonthYear_Sort", dim_date[MonthYear_Sort],
            "Year", dim_date[Year]
        )
        """
        dim_date_df = dax_to_df(run_dax_query(token, dax_date))
        dim_date_df.columns = dim_date_df.columns.str.replace(r"[\[\]]", "", regex=True)
        # ----- fact_opportunity -----
        dax_fact = """
        EVALUATE
        SELECTCOLUMNS(
            fact_opportunity,
            "Region", fact_opportunity[RegionSelector]
        )
        """
        fact_df = dax_to_df(run_dax_query(token, dax_fact))
        fact_df.columns = fact_df.columns.str.replace(r"[\[\]]", "", regex=True)


        # ----- Measures -----
        dax_measures = """
        EVALUATE
        ROW(
            "Revenue", [Revenue],
            "Win Rate", [Win Rate],
            "Average Sales Cycle (Won)", [Average Sales Cycle (Won)],
            "AI Influenced Win Rate", [AI Influenced Win Rate],
            "Total Opportunities", [Total Opportunities],
            "Won Opportunities", [Won Opps #],
            "Average Deal Size", [Average Deal Size],
            "AI Users", [AI Users],
            "AI Invocations", [AI Invocations],
            "Win More", [Win More (Total Opportunities)]
        )
        """
        measures_df = dax_to_df(run_dax_query(token, dax_measures))
        measures_df.columns = measures_df.columns.str.replace(r"[\[\]]", "", regex=True)
        st.success("✅ Data & measures loaded successfully")

    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")

# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(page_title="AI KPI Dashboard", layout="wide")
st.title("📊 AI KPI Dashboard")

# KPIs
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Win More", f"{"Win More":.1f}%")
col2.metric("Win Rate", f"{"Win Rate":.1f}%")
col3.metric("Avg Sales Cycle", f"{"Average Sales Cycle (Won)"} days")
col4.metric("Avg Deal Size", f"${"Average Deal Size":,.0f}")
col5.metric("AI Influenced Win Rate", f"{"AI Influenced Win Rate":.1f}%")

# Example 1: Bar chart of opportunities by region
if not fact_df.empty:
    st.subheader("🌍 Opportunities by Region")
    fig_region = px.histogram(fact_df, x="Region", title="Opportunities per Region")
    st.plotly_chart(fig_region)


