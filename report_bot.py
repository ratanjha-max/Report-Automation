import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Page configuration
st.set_page_config(page_title="DevRev UPHD Automator", layout="wide")

st.title("📊 DevRev Reporting Automation")

# --- TOKEN YAHAN SE FETCH HOGA (NO HARDCODED TOKEN) ---
try:
    # Ye line Streamlit Secrets se token uthayegi
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except Exception as e:
    st.error("Error: Secrets mein 'DEVREV_TOKEN' nahi mila. Dashboard ki settings check karein.")
    st.stop()

if st.button("Sync Live Data from DevRev"):
    with st.spinner("Fetching data from CRM..."):
        # DevRev API URL
        url = "https://api.devrev.ai/works.list"
        headers = {
            "Authorization": f"Bearer {DEVREV_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Converting JSON to Table
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # Pendency Calculation
                    # Note: Agar 'created_at' column name alag ho toh change kar sakte hain
                    if 'created_at' in df.columns:
                        df['created_at'] = pd.to_datetime(df['created_at'])
                        df['Aging (Days)'] = (datetime.now() - df['created_at']).dt.days
                    
                    st.subheader("📈 Pendency Pivot Table")
                    # Pivot Table: Status wise count
                    pivot = df.pivot_table(index='status', values='display_id', aggfunc='count', fill_value=0)
                    st.dataframe(pivot, use_container_width=True)

                    st.subheader("📝 Raw Data Preview")
                    st.write(df)
                else:
                    st.warning("No active tickets found in the response.")
            else:
                st.error(f"API Error: {response.status_code}")
                st.info("Check if your Token is valid or expired.")

        except Exception as err:
            st.error(f"Something went wrong: {err}")

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Paytm UPHD Internal Tool")
