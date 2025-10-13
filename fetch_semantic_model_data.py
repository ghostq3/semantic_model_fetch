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

TABLES = [
    "fact_opportunity",
    "fact_chatlogs",
    "dim_date",
    "chat_analysis",
    "chatfeedback",
    "Dim_ProductHierarchy",
    "Dim_c4c_accounts",
    "Dim_Emp_Hierarchy_SCD2"
]

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
# 🧠 Step 3. Fetch Each Table
# -------------------------------------
def fetch_table(table_name, access_token):
    dax_query = f"EVALUATE {table_name}"
    try:
        result = run_dax_query(access_token, dax_query)
        rows = result["results"][0]["tables"][0]["rows"]
        df = pd.DataFrame(rows)
        st.success(f"✅ Loaded {table_name} ({len(df)} rows)")
        return df
    except Exception as e:
        st.error(f"❌ Failed to fetch {table_name}: {e}")
        return None

# -------------------------------------
# ⚙️ Step 4. Main Streamlit App
# -------------------------------------
st.title("🔗 Power BI Semantic Model Data Loader")

if st.button("Load All Tables"):
    with st.spinner("Fetching Power BI data..."):
        token = get_access_token()
        all_data = {}

        for t in TABLES:
            df = fetch_table(t, token)
            if df is not None:
                all_data[t] = df

        # 🧮 Fetch measures (optional)
        try:
            dax_query = "EVALUATE ROW('Total Revenue', [Total Revenue], 'Total Chat Count', [Total Chats])"
            result = run_dax_query(token, dax_query)
            rows = result["results"][0]["tables"][0]["rows"]
            measures_df = pd.DataFrame(rows)
            all_data["*Measures"] = measures_df
            st.success("✅ Loaded measures table")
        except Exception as e:
            st.warning(f"⚠️ Measures query skipped or not found: {e}")

        st.write("### ✅ Loaded Tables:")
        st.json(list(all_data.keys()))
        
# -------------------------------------
# 🧮 Step 5. Fetch Measures
# -------------------------------------
def fetch_measures(access_token):
    # Replace measure names here
    dax_query = """
    EVALUATE ROW(
        "AI Invocations", [AI Invocations],
        "AI Users", [AI Users],
        "Average Deal Size", [Average Deal Size]
    )
    """
    try:
        result = run_dax_query(access_token, dax_query)
        rows = result["results"][0]["tables"][0]["rows"]
        df = pd.DataFrame(rows)
        st.success("✅ Loaded measures successfully")
        return df
    except Exception as e:
        st.error(f"❌ Failed to fetch measures: {e}")
        return None

# -------------------------------------
# 🧠 Example usage inside your button
# -------------------------------------
if st.button("Load All Tables"):
    with st.spinner("Fetching Power BI data..."):
        token = get_access_token()
        all_data = {}

        # Fetch tables
        for t in TABLES:
            df = fetch_table(t, token)
            if df is not None:
                all_data[t] = df

        # Fetch measures
        measures_df = fetch_measures(token)
        if measures_df is not None:
            all_data["*Measures"] = measures_df

        st.write("### ✅ Loaded Data:")
        st.json(list(all_data.keys()))
        st.dataframe(measures_df)
