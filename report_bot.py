import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone # Timezone import kiya

st.set_page_config(page_title="DevRev Automator", layout="wide")
st.title("📊 DevRev Reporting Automation")

# Token fetch from Secrets
try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets mein 'DEVREV_TOKEN' nahi mila!")
    st.stop()

if st.button("Sync Live Data from DevRev"):
    with st.spinner("Fetching data..."):
        url = "https://api.devrev.ai/works.list"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    cols = df.columns.tolist()
                    
                    # --- FIX: TIMEZONE NAIVE vs AWARE ERROR ---
                    date_col = next((c for c in cols if 'created_date' in c.lower()), None)
                    if date_col:
                        # 1. Date ko datetime mein convert karo (UTC ke saath)
                        df[date_col] = pd.to_datetime(df[date_col], utc=True)
                        
                        # 2. Aaj ki date ko bhi UTC 'Aware' banao
                        now_utc = datetime.now(timezone.utc)
                        
                        # 3. Ab subtraction safely ho jayega
                        df['Aging (Days)'] = (now_utc - df[date_col]).dt.days
                    
                    # --- PIVOT LOGIC ---
                    status_col = next((c for c in cols if 'stage.name' in c.lower() or 'status' in c.lower()), None)
                    
                    st.subheader("📈 Ticket Pendency Pivot")
                    if status_col:
                        pivot = df.groupby(status_col).size().reset_index(name='Count')
                        st.table(pivot)
                    else:
                        st.warning("Status column (Stage) nahi mila.")

                    st.subheader("📝 Detailed Data Preview")
                    st.dataframe(df, use_container_width=True)
                    
                    # Download link
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Full CSV", data=csv, file_name="devrev_export.csv")
                else:
                    st.warning("API response empty hai.")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"System Error: {str(e)}")

st.sidebar.write("Connected to DevRev ✅")
