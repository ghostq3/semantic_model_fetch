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
# 🔑 Get Access Token
# -------------------------------------
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# -------------------------------------
# 📊 Run DAX Query
# -------------------------------------
def run_dax_query(token, dax_query):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"queries": [{"query": dax_query}]}
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()

def dax_to_df(result_json):
    try:
        rows = result_json["results"][0]["tables"][0]["rows"]
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

# -------------------------------------
# ⚙️ Main Streamlit App
# -------------------------------------
st.set_page_config(page_title="AI Sales Insights", layout="wide")
st.title("🤖 AI Sales Insights Dashboard")

if st.button("Load Data"):
    with st.spinner("Fetching Power BI data..."):
        try:
            token = get_access_token()

            # --- Helper to safely get a measure
            def try_measure(name):
                try:
                    dax = f"EVALUATE ROW(\"{name}\", [{name}])"
                    df = dax_to_df(run_dax_query(token, dax))
                    if not df.empty:
                        val = list(df.iloc[0])[0]
                        st.write(f"✅ Loaded measure: {name} = {val}")
                        return val
                except Exception:
                    st.write(f"⚠️ Skipped missing measure: {name}")
                return None

            # --- Try all required measures
            measures = {
                "Revenue": try_measure("Revenue"),
                "Win Rate": try_measure("Win Rate"),
                "Average Sales Cycle (Won)": try_measure("Average Sales Cycle (Won)"),
                "AI Influenced Win Rate": try_measure("AI Influenced Win Rate"),
                "Total Opportunities": try_measure("Total Opportunities"),
                "Won Opps #": try_measure("Won Opps #"),
                "Average Deal Size": try_measure("Average Deal Size"),
                "AI Users": try_measure("AI Users"),
                "AI Invocations": try_measure("AI Invocations"),
            }

            st.divider()

            # --- Cards (AI metrics)
            col1, col2 = st.columns(2)
            col1.metric("🧠 AI Users", f"{measures.get('AI Users', 0):,}")
            col2.metric("⚙️ AI Invocations", f"{measures.get('AI Invocations', 0):,}")

            # --- Sales Trend
            dax_sales = """
            EVALUATE
            SUMMARIZECOLUMNS(
                dim_date[MonthYear],
                "Revenue", [Revenue]
            )
            """
            sales_df = dax_to_df(run_dax_query(token, dax_sales))
            if not sales_df.empty:
                st.subheader("📈 Sales Trend Over Time")
                st.plotly_chart(
                    px.line(sales_df, x="MonthYear", y="Revenue", markers=True),
                    use_container_width=True
                )

            # --- Win Rate by Region
            dax_region = """
            EVALUATE
            SUMMARIZECOLUMNS(
                fact_opportunity[RegionSelector],
                "Win Rate", [Win Rate]
            )
            """
            region_df = dax_to_df(run_dax_query(token, dax_region))
            if not region_df.empty:
                st.subheader("💰 Win Rate by Region")
                st.plotly_chart(
                    px.bar(region_df, x="RegionSelector", y="Win Rate", color="RegionSelector"),
                    use_container_width=True
                )

            # --- AI Influence vs Total Deals
            if measures["AI Influenced Win Rate"] is not None and measures["Total Opportunities"] is not None:
                ai_df = pd.DataFrame({
                    "AI Influenced Win Rate": [measures["AI Influenced Win Rate"]],
                    "Total Opportunities": [measures["Total Opportunities"]]
                })
                st.subheader("🧠 AI Influence vs Total Deals")
                st.plotly_chart(
                    px.scatter(ai_df, x="Total Opportunities", y="AI Influenced Win Rate",
                               size="Total Opportunities", color="AI Influenced Win Rate"),
                    use_container_width=True
                )

            # --- Average Sales Cycle Trend
            dax_cycle = """
            EVALUATE
            SUMMARIZECOLUMNS(
                dim_date[MonthYear],
                "Average Sales Cycle (Won)", [Average Sales Cycle (Won)]
            )
            """
            cycle_df = dax_to_df(run_dax_query(token, dax_cycle))
            if not cycle_df.empty:
                st.subheader("⏱️ Average Sales Cycle Trend")
                st.plotly_chart(
                    px.line(cycle_df, x="MonthYear", y="Average Sales Cycle (Won)", markers=True),
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"❌ Failed to fetch data: {e}")
