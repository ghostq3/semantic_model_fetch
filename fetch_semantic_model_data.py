import streamlit as st
import requests
import pandas as pd
import json

st.title("📊 Fetch Power BI Semantic Model Table (fact_opportunity)")

# ----------------------------
# 🔐 Secrets (set in Streamlit)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]

WORKSPACE_ID = "9755694b-649e-4a01-8386-eee2bd91079e"
DATASET_ID = "5b64ca41-91bd-4db4-b005-0c0327887b5e"

# Using Power BI REST API for dataset queries
RESOURCE = "https://analysis.windows.net/powerbi/api"

# ----------------------------
# 1️⃣ Get Access Token
# ----------------------------
@st.cache_data(ttl=3600)
def get_access_token():
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE
    }
    res = requests.post(token_url, data=data)
    res.raise_for_status()
    return res.json()["access_token"]

try:
    token = get_access_token()
    st.success("✅ Access token acquired")
except Exception as e:
    st.error(f"❌ Failed to get token: {e}")
    st.stop()

# ----------------------------
# 2️⃣ Query the dataset using DAX
# ----------------------------
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

query_url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"

# DAX query — adjust TOPN for performance
query_body = {
    "queries": [
        {
            "query": "EVALUATE TOPN(50, fact_opportunity)"
        }
    ],
    "serializerSettings": {"inculdeNulls": True}
}

if st.button("📥 Fetch fact_opportunity Data"):
    try:
        response = requests.post(query_url, headers=headers, json=query_body)
        response.raise_for_status()
        data = response.json()

        # Extract table rows
        if "results" in data and data["results"]:
            tables = data["results"][0]["tables"]
            if tables and "rows" in tables[0]:
                df = pd.DataFrame(tables[0]["rows"])
                st.dataframe(df)
                st.success(f"✅ Retrieved {len(df)} rows from fact_opportunity")
            else:
                st.warning("⚠️ No rows found.")
        else:
            st.warning("⚠️ No results returned. Check table name or access.")
    except Exception as e:
        st.error(f"❌ Query failed: {e}")
