import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import datetime

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

        # Helper to run and clean queries
        def fetch_table(query):
            df = dax_to_df(run_dax_query(token, query))
            df.columns = df.columns.str.replace(r"[\[\]]", "", regex=True)
            return df

        # ---------- DIMENSIONS ----------
        dax_date = "EVALUATE dim_date"
        dim_date_df = fetch_table(dax_date)
        dim_date_df.columns = dim_date_df.columns.str.replace("dim_date", "", regex=False)
        
        dax_emp = "EVALUATE Dim_Emp_Hierarchy_SCD2"
        dim_emp_df = fetch_table(dax_emp)
        dim_emp_df.columns = dim_emp_df.columns.str.replace("Dim_Emp_Hierarchy_SCD2", "", regex=False)
        
        dax_accounts = "EVALUATE Dim_c4c_accounts"
        dim_accounts_df = fetch_table(dax_accounts)
        dim_accounts_df.columns = dim_accounts_df.columns.str.replace("Dim_c4c_accounts", "", regex=False)
        
        dax_product = "EVALUATE Dim_ProductHierarchy"
        dim_product_df = fetch_table(dax_product)
        dim_product_df.columns = dim_product_df.columns.str.replace("Dim_ProductHierarchy", "", regex=False)
        
        
        # ---------- FACTS ----------
        dax_chat = "EVALUATE fact_chatlogs"
        fact_chat_df = fetch_table(dax_chat)
        fact_chat_df.columns = fact_chat_df.columns.str.replace("fact_chatlogs", "", regex=False)
        
        dax_opp = "EVALUATE fact_opportunity"
        fact_opp_df = fetch_table(dax_opp)
        fact_opp_df.columns = fact_opp_df.columns.str.replace("fact_opportunity", "", regex=False)
        
        dax_feedback = "EVALUATE chatfeedback"
        chat_feedback_df = fetch_table(dax_feedback)
        chat_feedback_df.columns = chat_feedback_df.columns.str.replace("chatfeedback", "", regex=False)
        
        dax_analysis = "EVALUATE chat_analysis"
        chat_analysis_df = fetch_table(dax_analysis)
        chat_analysis_df.columns = chat_analysis_df.columns.str.replace("chat_analysis", "", regex=False)


    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")

#Measures
st.write("fact_opportunity columns:", fact_opp_df.columns.tolist())

# total_opportunities = fact_opp_df["OpportunityID"].nunique()

# # Count opportunities where LifecycleStatus = "Won" and CloseDate <= today
# today = datetime.date.today()
# won_opps_df = fact_opp_df[
#     (fact_opp_df["LifecycleStatus"] == "Won") &
#     (pd.to_datetime(fact_opp_df["CloseDate"]) <= pd.Timestamp(today))
# ]
# won_opps = len(won_opps_df)

# ai_users = fact_chat_df["user_id"].nunique()

# # Get list of AI user emails from chat logs
# ai_user_emails = set(fact_chat_df["user_email"].dropna().unique())

# # Merge employee hierarchy to map Employee Email to opportunities
# fact_opp_with_emp = fact_opp_df.merge(
#     dim_emp_df[["Employee Email"]], how="left", left_on="OwnerEmail", right_on="Employee Email"
# )

# # Filter to AI-influenced deals
# ai_influenced_df = fact_opp_with_emp[
#     fact_opp_with_emp["Employee Email"].isin(ai_user_emails)
# ]

# # Calculate AI Influenced Win Rate
# won_count = (ai_influenced_df["LifecycleStatus"] == "Won").sum()
# lost_count = (ai_influenced_df["LifecycleStatus"] == "Lost").sum()

# ai_influenced_win_rate = (
#     won_count / (won_count + lost_count) * 100
#     if (won_count + lost_count) > 0 else 0
# )


# # Define helper to calculate close rate
# def calc_close_rate(df):
#     won = (df["LifecycleStatus"] == "Won").sum()
#     lost = (df["LifecycleStatus"] == "Lost").sum()
#     return won / (won + lost) if (won + lost) > 0 else 0

# # Add Year column if missing
# fact_opp_df["CloseDate"] = pd.to_datetime(fact_opp_df["CloseDate"])
# fact_opp_df["Year"] = fact_opp_df["CloseDate"].dt.year

# current_year = fact_opp_df["Year"].max()
# prev_year = current_year - 1

# current_rate = calc_close_rate(fact_opp_df[fact_opp_df["Year"] == current_year])
# prev_rate = calc_close_rate(fact_opp_df[fact_opp_df["Year"] == prev_year])

# close_rate_reduction = prev_rate - current_rate

# filtered_df = fact_opp_df[
#     fact_opp_df["ReasonForStatus"] != "Closed...Too Many Days in a Single Sales Stage"
# ]

# won = (filtered_df["LifecycleStatus"] == "Won").sum()
# lost = (filtered_df["LifecycleStatus"] == "Lost").sum()

# win_rate = won / (won + lost) if (won + lost) > 0 else 0

# win_more = won / total_opportunities if total_opportunities > 0 else 0

# avg_deal_size = fact_opp_df["NegotiatedValue"].mean()

# fact_opp_df["CreatedOn"] = pd.to_datetime(fact_opp_df["CreatedOn"])
# fact_opp_df["CloseDate"] = pd.to_datetime(fact_opp_df["CloseDate"])

# won_df = fact_opp_df[fact_opp_df["LifecycleStatus"] == "Won"].copy()
# won_df["SalesCycleDays"] = (won_df["CloseDate"] - won_df["CreatedOn"]).dt.days

# avg_sales_cycle_won = won_df["SalesCycleDays"].mean()

# for k, v in metrics.items():
#     if isinstance(v, float):
#         st.metric(k, f"{v:,.2f}")
#     else:
#         st.metric(k, f"{v:,}")


# ----------------------------
# Streamlit App
# ----------------------------
# st.set_page_config(page_title="AI KPI Dashboard", layout="wide")
# st.title("📊 AI KPI Dashboard")

# # KPIs
# # Extract measures as variables
# win_more = measures_df.at[0, "Win More"] * 100
# win_rate = measures_df.at[0, "Win Rate"] * 100
# avg_sales_cycle = measures_df.at[0, "Average Sales Cycle (Won)"]
# avg_deal_size = measures_df.at[0, "Average Deal Size"]
# ai_influenced_win_rate = measures_df.at[0, "AI Influenced Win Rate"] * 100

# # Display KPIs
# col1, col2, col3, col4, col5 = st.columns(5)
# col1.metric("Win More", f"{win_more:.1f}%")
# col2.metric("Win Rate", f"{win_rate:.1f}%")
# col3.metric("Avg Sales Cycle", f"{avg_sales_cycle:.0f} days") 
# col4.metric("Avg Deal Size", f"${avg_deal_size:,.0f}")
# col5.metric("AI Influenced Win Rate", f"{ai_influenced_win_rate:.1f}%")


# # Bar Chart Per Opp
# if not fact_df.empty:
#     st.subheader("🌍 Opportunities by Region (Including AI Influenced)")

#     # Summarize total opportunities per region
#     region_summary = fact_df.groupby("Region").agg(
#         Total_Opps=("Region", "count")  # replace with actual opportunity count column if needed
#     ).reset_index()

#     # Compute AI-influenced opportunities using the measure
#     region_summary["AI_Influenced_Opps"] = region_summary["Total_Opps"] * measures_df.at[0, "AI Influenced Win Rate"]
#     region_summary["Non_AI_Opps"] = region_summary["Total_Opps"] - region_summary["AI_Influenced_Opps"]

#     # Melt for stacked bar
#     plot_df = region_summary.melt(
#         id_vars="Region",
#         value_vars=["Non_AI_Opps", "AI_Influenced_Opps"],
#         var_name="Type",
#         value_name="Opportunities"
#     )

#     # Plot with custom colors
#     fig_region = px.bar(
#         plot_df,
#         x="Region",
#         y="Opportunities",
#         color="Type",
#         title="Opportunities per Region (AI Influenced vs Others)",
#         barmode="stack",
#         labels={"Type": "Opportunity Type"},
#         color_discrete_map={
#             "Non_AI_Opps": "#006771",
#             "AI_Influenced_Opps": "#FF9999"
#         }
#     )

#     st.plotly_chart(fig_region)
