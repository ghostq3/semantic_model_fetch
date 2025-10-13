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
# ⚙️ Step 4. Main Streamlit App
# -------------------------------------
st.title("🔗 Power BI Semantic Model – Test Required Fields + Measures")

if st.button("Run Data Fetch Test"):
    with st.spinner("Fetching Power BI data..."):
        try:
            token = get_access_token()

            # 🗓️ dim_date
            dax_date = """
            EVALUATE
            SELECTCOLUMNS(
                dim_date,
                "MonthYear", dim_date[MonthYear],
                "MonthYear_Sort", dim_date[MonthYear_Sort],
                "Year", dim_date[Year]
            )
            """
            date_result = run_dax_query(token, dax_date)
            dim_date_df = dax_to_df(date_result)
            st.success(f"✅ dim_date loaded ({len(dim_date_df)} rows)")
            st.dataframe(dim_date_df.head())

            # 🌍 fact_opportunity (Region only)
            dax_fact = """
            EVALUATE
            SELECTCOLUMNS(
                fact_opportunity,
                "Region", fact_opportunity[RegionSelector]
            )
            """
            fact_result = run_dax_query(token, dax_fact)
            fact_df = dax_to_df(fact_result)
            st.success(f"✅ fact_opportunity loaded ({len(fact_df)} rows)")
            st.dataframe(fact_df.head())

            # 🧮 *Measures (includes all KPIs)
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
            measures_result = run_dax_query(token, dax_measures)
            measures_df = dax_to_df(measures_result)
            st.success("✅ *Measures loaded successfully")
            st.dataframe(measures_df)

        except Exception as e:
            st.error(f"❌ Failed to fetch data: {e}")
