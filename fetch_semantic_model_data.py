import streamlit as st
import requests
import pandas as pd

# ----------------------------
# 🔐 Secrets (set in Streamlit Cloud)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]
RESOURCE = "https://analysis.windows.net/powerbi/api"

# Workspace & Dataset IDs
WORKSPACE_ID = "9755694b-649e-4a01-8386-eee2bd91079e"
DATASET_ID = "5b64ca41-91bd-4db4-b005-0c0327887b5e"

# Tables you want to include
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
# 🔑 Get Access Token
# ----------------------------
token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "resource": RESOURCE,
}

st.title("📊 Fabric Semantic Model Metadata Explorer")

st.write("Getting access token...")
token_resp = requests.post(token_url, data=token_data)

if token_resp.status_code != 200:
    st.error(f"Failed to get token: {token_resp.text}")
    st.stop()

access_token = token_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
st.success("✅ Token acquired successfully!")

# ----------------------------
# 🧩 Get Dataset Metadata
# ----------------------------
meta_url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/tables"
st.write("Fetching dataset metadata...")

meta_resp = requests.get(meta_url, headers=headers)
if meta_resp.status_code != 200:
    st.error(f"Failed to get metadata: {meta_resp.text}")
    st.stop()

meta_data = meta_resp.json().get("value", [])

# ----------------------------
# 🧮 Filter Tables
# ----------------------------
filtered_tables = [t for t in meta_data if t["name"] in INCLUDE_TABLES]

if not filtered_tables:
    st.warning("No matching tables found in dataset.")
else:
    st.success(f"✅ Found {len(filtered_tables)} matching tables.")
    for table in filtered_tables:
        st.subheader(f"📘 {table['name']}")
        if "columns" in table:
            cols = [col["name"] for col in table["columns"]]
            st.write("**Columns:**")
            st.dataframe(pd.DataFrame(cols, columns=["Column Name"]))
        else:
            st.info("No columns available for this table.")
