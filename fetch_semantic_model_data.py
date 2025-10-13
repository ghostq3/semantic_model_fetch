import streamlit as st
import requests

st.title("🔍 Power BI Service Principal Access Tester")

# --- Load secrets ---
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]
RESOURCE = st.secrets["FABRIC_RESOURCE"]

# --- Token request ---
st.write("Requesting access token...")

token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "resource": RESOURCE,
}

token_resp = requests.post(token_url, data=token_data)
if token_resp.status_code != 200:
    st.error(f"Failed to get token: {token_resp.text}")
    st.stop()

access_token = token_resp.json()["access_token"]
st.success("✅ Token acquired successfully!")

# --- Headers for Power BI REST API ---
headers = {"Authorization": f"Bearer {access_token}"}

# --- Get workspaces ---
st.write("Fetching accessible workspaces...")

groups_url = "https://api.powerbi.com/v1.0/myorg/groups"
groups_resp = requests.get(groups_url, headers=headers)

if groups_resp.status_code != 200:
    st.error(f"❌ Failed to get workspaces: {groups_resp.text}")
    st.stop()

groups_data = groups_resp.json().get("value", [])

if not groups_data:
    st.warning("⚠️ No workspaces found. Your service principal might not have access to any.")
else:
    st.success(f"✅ Found {len(groups_data)} accessible workspace(s).")
    for g in groups_data:
        st.write(f"- **{g['name']}** (ID: {g['id']})")

    # --- Optionally, list datasets per workspace ---
    st.subheader("Datasets per Workspace")
    for g in groups_data:
        ws_id = g["id"]
        ds_url = f"https://api.powerbi.com/v1.0/myorg/groups/{ws_id}/datasets"
        ds_resp = requests.get(ds_url, headers=headers)
        if ds_resp.status_code == 200:
            datasets = ds_resp.json().get("value", [])
            if datasets:
                st.markdown(f"### 📊 {g['name']}")
                for ds in datasets:
                    st.write(f"• {ds['name']} — *(ID: {ds['id']})*")
