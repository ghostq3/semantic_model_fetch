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

    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")

# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(page_title="AI KPI Dashboard", layout="wide")
st.title("📊 AI KPI Dashboard")

# KPIs
# Extract measures as variables
win_more = measures_df.at[0, "Win More"] * 100
win_rate = measures_df.at[0, "Win Rate"] * 100
avg_sales_cycle = measures_df.at[0, "Average Sales Cycle (Won)"]
avg_deal_size = measures_df.at[0, "Average Deal Size"]
ai_influenced_win_rate = measures_df.at[0, "AI Influenced Win Rate"] * 100

# Display KPIs
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Win More", f"{win_more:.1f}%")
col2.metric("Win Rate", f"{win_rate:.1f}%")
col3.metric("Avg Sales Cycle", f"{avg_sales_cycle:.0f} days") 
col4.metric("Avg Deal Size", f"${avg_deal_size:,.0f}")
col5.metric("AI Influenced Win Rate", f"{ai_influenced_win_rate:.1f}%")

# Bar Chart Per Opp
if not fact_df.empty:
    st.subheader("🌍 Opportunities by Region (Including AI Influenced)")

    # Summarize total opportunities per region
    region_summary = fact_df.groupby("Region").agg(
        Total_Opps=("Region", "count")  # or replace with actual opportunity count column
    ).reset_index()

    # Compute AI-influenced opportunities using the measure
    region_summary["AI_Influenced_Opps"] = region_summary["Total_Opps"] * measures_df.at[0, "AI Influenced Win Rate"]
    region_summary["Non_AI_Opps"] = region_summary["Total_Opps"] - region_summary["AI_Influenced_Opps"]

    # Melt for stacked bar
    plot_df = region_summary.melt(
        id_vars="Region",
        value_vars=["Non_AI_Opps", "AI_Influenced_Opps"],
        var_name="Type",
        value_name="Opportunities"
    )

    # Plot
    fig_region = px.bar(
        plot_df,
        x="Region",
        y="Opportunities",
        color="Type",
        title="Opportunities per Region (AI Influenced vs Others)",
        barmode="stack",
        labels={"Type": "Opportunity Type"}
    )

    # Set custom colors
    fig_region.update_traces(marker_color=["#006771", "#FF9999"])

    st.plotly_chart(fig_region)




