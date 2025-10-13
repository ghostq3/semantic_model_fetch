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
# ⚙️ Step 4. Main Streamlit App
# -------------------------------------
st.set_page_config(page_title="AI Sales Insights", layout="wide")
st.title("🤖 AI Sales Insights Dashboard")

if st.button("Load Data"):
    with st.spinner("Fetching Power BI data..."):
        try:
            token = get_access_token()

            # 🗓️ Date table
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

            # 🌍 Region from fact_opportunity
            dax_fact = """
            EVALUATE
            SELECTCOLUMNS(
                fact_opportunity,
                "Region", fact_opportunity[RegionSelector]
            )
            """
            fact_df = dax_to_df(run_dax_query(token, dax_fact))

            # 🧮 Measures
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
                "AI Invocations", [AI Invocations]
            )
            """
            measures_df = dax_to_df(run_dax_query(token, dax_measures))

            # 🧍 AI Users & Invocations Cards
            col1, col2 = st.columns(2)
            col1.metric("🧠 AI Users", f"{measures_df['AI Users'][0]:,.0f}")
            col2.metric("⚙️ AI Invocations", f"{measures_df['AI Invocations'][0]:,.0f}")

            # 📈 Sales Trend (Revenue over MonthYear)
            dax_trend = """
            EVALUATE
            SUMMARIZECOLUMNS(
                dim_date[MonthYear],
                "Revenue", [Revenue]
            )
            """
            sales_trend_df = dax_to_df(run_dax_query(token, dax_trend))
            st.subheader("📈 Sales Trend Over Time")
            st.plotly_chart(
                px.line(
                    sales_trend_df,
                    x="MonthYear",
                    y="Revenue",
                    title="Revenue Trend by Month",
                    markers=True
                ),
                use_container_width=True
            )

            # 💰 Win Rate by Region
            dax_region = """
            EVALUATE
            SUMMARIZECOLUMNS(
                fact_opportunity[RegionSelector],
                "Win Rate", [Win Rate]
            )
            """
            region_df = dax_to_df(run_dax_query(token, dax_region))
            st.subheader("💰 Win Rate by Region")
            st.plotly_chart(
                px.bar(
                    region_df,
                    x="RegionSelector",
                    y="Win Rate",
                    color="RegionSelector",
                    title="Win Rate by Region"
                ),
                use_container_width=True
            )

            # 🧠 AI Influence vs. Total Deals (Scatter)
            dax_ai = """
            EVALUATE
            ROW(
                "AI Influenced Win Rate", [AI Influenced Win Rate],
                "Total Opportunities", [Total Opportunities]
            )
            """
            ai_df = dax_to_df(run_dax_query(token, dax_ai))
            st.subheader("🧠 AI Influence vs Total Deals")
            st.plotly_chart(
                px.scatter(
                    ai_df,
                    x="Total Opportunities",
                    y="AI Influenced Win Rate",
                    size="Total Opportunities",
                    color="AI Influenced Win Rate",
                    title="AI Influence vs Total Deals"
                ),
                use_container_width=True
            )

            # ⏱️ Average Sales Cycle Trend
            dax_cycle = """
            EVALUATE
            SUMMARIZECOLUMNS(
                dim_date[MonthYear],
                "Average Sales Cycle (Won)", [Average Sales Cycle (Won)]
            )
            """
            cycle_df = dax_to_df(run_dax_query(token, dax_cycle))
            st.subheader("⏱️ Average Sales Cycle Trend")
            st.plotly_chart(
                px.line(
                    cycle_df,
                    x="MonthYear",
                    y="Average Sales Cycle (Won)",
                    markers=True,
                    title="Average Sales Cycle (Won) Over Time"
                ),
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Failed to fetch data: {e}")
