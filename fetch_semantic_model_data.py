import streamlit as st
import requests
import pandas as pd
import json
from time import sleep

st.title("📊 Power BI Semantic Model Data Loader (with Measures)")

# ----------------------------
# 🔐 Secrets (set in Streamlit)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]

WORKSPACE_ID = "9755694b-649e-4a01-8386-eee2bd91079e"
DATASET_ID = "5b64ca41-91bd-4db4-b005-0c0327887b5e"

RESOURCE = "https://analysis.windows.net/powerbi/api"

# Tables to include
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
# 2️⃣ Query function for a table
# ----------------------------
def fetch_table(table_name, limit=100):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    query = {"queries": [{"query": f"EVALUATE TOPN({limit}, '{table_name}')"}]}
    res = requests.post(url, headers=headers, json=query)
    if res.status_code != 200:
        raise Exception(f"{res.status_code} - {res.text}")
    result = res.json()
    if not result.get("results"):
        return pd.DataFrame()
    table = result["results"][0]["tables"][0]
    return pd.DataFrame(table["rows"])

# ----------------------------
# 3️⃣ Fetch Measures metadata
# ----------------------------
def fetch_measures():
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/tables"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    tables = res.json().get("value", [])
    measures = []
    for tbl in tables:
        if "measures" in tbl:
            for m in tbl["measures"]:
                measures.append({
                    "table": tbl["name"],
                    "measureName": m["name"],
                    "expression": m["expression"]
                })
    return pd.DataFrame(measures)

# ----------------------------
# 4️⃣ Run fetch
# ----------------------------
if st.button("📥 Load All Tables & Measures"):
    st.info("Fetching data from semantic model… please wait ⏳")

    dfs = {}
    for t in TABLES:
        with st.spinner(f"Fetching {t}..."):
            try:
                df = fetch_table(t)
                dfs[t] = df
                st.success(f"✅ {t} — {len(df)} rows")
                st.dataframe(df.head(10))
            except Exception as e:
                st.error(f"❌ Failed to fetch {t}: {e}")
            sleep(1)

    # Fetch measures
    with st.spinner("Fetching *Measures..."):
        try:
            measures_df = fetch_measures()
            dfs["*Measures"] = measures_df
            st.success(f"✅ Retrieved {len(measures_df)} measures")
            st.dataframe(measures_df)
        except Exception as e:
            st.error(f"❌ Failed to fetch measures: {e}")

    st.success("🎉 All tables & measures loaded!")
    st.write("✅ Available DataFrames:", list(dfs.keys()))
