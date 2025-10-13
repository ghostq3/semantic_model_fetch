import streamlit as st
import requests
import json

st.title("🔄 Power BI Dataset Refresh Status")

# ----------------------------
# 🔐 Secrets (set in Streamlit)
# ----------------------------
TENANT_ID = st.secrets["FABRIC_TENANT_ID"]
CLIENT_ID = st.secrets["FABRIC_CLIENT_ID"]
CLIENT_SECRET = st.secrets["FABRIC_CLIENT_SECRET"]

WORKSPACE_ID = "205b187c-31f8-4789-bde3-5a92628392a1"
DATASET_ID = "f5257086-90d3-4106-8e59-6f4b59ad4d19"

RESOURCE = "https://analysis.windows.net/powerbi/api"

# ----------------------------
# 1️⃣ Get Access Token
# ----------------------------
@st.cache_data(ttl=3600)
def get_access_token():
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "resource": RESOURCE
    }
    res = requests.post(token_url, data=token_data)
    res.raise_for_status()
    return res.json()["access_token"]

try:
    access_token = get_access_token()
    st.success("✅ Access token acquired")
except Exception as e:
    st.error(f"❌ Failed to get token: {e}")
    st.stop()

# ----------------------------
# 2️⃣ Fetch last refresh status
# ----------------------------
url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE_ID}/datasets/{DATASET_ID}/refreshes?$top=1"
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

if st.button("🔍 Check Last Refresh Status"):
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

        if data.get("value"):
            last_refresh = data["value"][0]
            st.json(last_refresh)
            st.success(f"✅ Last Refresh Status: {last_refresh['status']}")
        else:
            st.warning("No refresh history found.")
    except Exception as e:
        st.error(f"❌ Failed to fetch refresh data: {e}")
