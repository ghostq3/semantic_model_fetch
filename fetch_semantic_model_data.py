import streamlit as st
import requests
import pandas as pd

# ----------------------------
# 🔒 Load Fabric Credentials from Secrets
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]
RESOURCE = st.secrets["FABRIC_RESOURCE"]
WORKSPACE_ID = st.secrets["FABRIC_WORKSPACE_ID"]
SEMANTIC_MODEL_ID = st.secrets["FABRIC_SEMANTIC_MODEL_ID"]

# ----------------------------
# ⚙️ Configuration: Tables to Include
# ----------------------------
TARGET_TABLES = [
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
# 🧾 Get Access Token
# ----------------------------
@st.cache_data(ttl=3300)
def get_fabric_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE,
    }
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        st.error(f"Token request failed: {resp.text}")
        st.stop()
    return resp.json()["access_token"]

# ----------------------------
# 📦 Get Semantic Model Metadata
# ----------------------------
def get_semantic_model_metadata(workspace_id, model_id, token):
    api_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels/{model_id}/tables"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        st.error(f"Metadata fetch failed: {resp.text}")
        st.stop()
    return resp.json()

# ----------------------------
# 🧮 Extract Columns and Measures (Filtered)
# ----------------------------
def extract_filtered_metadata(metadata_json, allowed_tables):
    tables = metadata_json.get("value", [])
    data = []
    for table in tables:
        table_name = table.get("name")
        if table_name not in allowed_tables:
            continue  # skip any tables not in the list
        for col in table.get("columns", []):
            data.append({
                "Table": table_name,
                "Name": col.get("name"),
                "Type": "Column",
                "DataType": col.get("dataType")
            })
        for measure in table.get("measures", []):
            data.append({
                "Table": table_name,
                "Name": measure.get("name"),
                "Type": "Measure",
                "Expression": measure.get("expression")
            })
    return pd.DataFrame(data)

# ----------------------------
# 🧭 Streamlit UI
# ----------------------------
st.set_page_config(page_title="Fabric Semantic Model Explorer", layout="wide")
st.title("🔍 Microsoft Fabric Semantic Model Explorer (Filtered)")
st.write("This app connects securely to your Fabric semantic model and retrieves only selected tables and measures.")

if st.button("Fetch Selected Tables"):
    with st.spinner("Authenticating and fetching model metadata..."):
        token = get_fabric_token()
        metadata = get_semantic_model_metadata(WORKSPACE_ID, SEMANTIC_MODEL_ID, token)
        df = extract_filtered_metadata(metadata, TARGET_TABLES)
        if df.empty:
            st.warning("No data found for the selected tables. Check your table names or permissions.")
        else:
            st.success(f"✅ Retrieved {len(df)} entries successfully.")
            st.dataframe(df, use_container_width=True)

            # Filter dropdowns for easy search
            st.subheader("🔎 Filter Results")
            table_choice = st.selectbox("Filter by Table", ["All"] + sorted(df["Table"].unique()))
            type_choice = st.selectbox("Filter by Type", ["All", "Column", "Measure"])

            filtered_df = df.copy()
            if table_choice != "All":
                filtered_df = filtered_df[filtered_df["Table"] == table_choice]
            if type_choice != "All":
                filtered_df = filtered_df[filtered_df["Type"] == type_choice]

            st.dataframe(filtered_df, use_container_width=True)

            # Download CSV
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "fabric_filtered_metadata.csv", "text/csv")
