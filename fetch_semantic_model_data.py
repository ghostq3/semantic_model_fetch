import streamlit as st
import requests
import pandas as pd

st.title("📊 Power BI Dataset Data Fetcher")

# ----------------------------
# 🔐 Secrets (Streamlit Cloud)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]
RESOURCE = "https://analysis.windows.net/powerbi/api"

# Workspace & Dataset IDs
WORKSPACE_ID = "9755694b-649e-4a01-8386-eee2bd91079e"
DATASET_ID = "5b64ca41-91bd-4db4-b005-0c0327887b5e"

# Tables to include
INCLUDE_TABLES = [
    "fact_opportunity",
    "fact_chatlogs",
    "dim_date",
    "chat_analysis",
    "chatfeedback",
    "Dim_ProductHierarchy",
    "Dim_c4c_accounts",
    "Dim_Emp_Hierarchy_SCD2",
    "*Measures"
]

# ----------------------------
# 🪙 Get Access Token
# ----------------------------
@st.cache_data(ttl=3500)
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": f"{RESOURCE}/.default"
    }
    res = requests.post(url, data=payload)
    res.raise_for_status()
    return res.json()["access_token"]

# ----------------------------
# 📥 Run DAX Query
# ----------------------------
def run_dax_query(query: str):
    token = get_access_token()
    url = f"https://api.fabric.microsoft.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {"queries": [{"query": query}]}
    res = requests.post(url, headers=headers, json=body)
    res.raise_for_status()
    result = res.json()

    # Handle empty or unexpected results
    try:
        rows = result["results"][0]["tables"][0]["rows"]
        return pd.DataFrame(rows)
    except (KeyError, IndexError):
        st.warning("⚠️ No data returned or invalid query format.")
        return pd.DataFrame()

# ----------------------------
# 🚀 UI
# ----------------------------
st.sidebar.header("Settings")
selected_tables = st.sidebar.multiselect(
    "Select tables to fetch",
    INCLUDE_TABLES,
    default=INCLUDE_TABLES
)

if st.button("Fetch Selected Tables"):
    token = get_access_token()
    st.success("✅ Connected successfully to Power BI.")
    
    for table in selected_tables:
        with st.expander(f"📄 {table}", expanded=False):
            query = f"EVALUATE {table}" if table != "*Measures" else "EVALUATE SUMMARIZECOLUMNS('Measures'[Name], 'Measures'[Value])"
            try:
                df = run_dax_query(query)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label=f"⬇️ Download {table}.csv",
                        data=csv,
                        file_name=f"{table}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No data found in {table}.")
            except Exception as e:
                st.error(f"❌ Failed to fetch {table}: {str(e)}")

st.caption("🔒 Requires Build permission on the Power BI dataset and Dataset.Read.All API permission in Azure AD.")
