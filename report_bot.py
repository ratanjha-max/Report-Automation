import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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
                # Use json_normalize to flatten nested structures
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # --- DYNAMIC COLUMN FIX ---
                    cols = df.columns.tolist()
                    
                    # 1. Pendency Check (Created Date dhundna)
                    date_col = next((c for c in cols if 'created_date' in c.lower()), None)
                    if date_col:
                        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        df['Aging (Days)'] = (datetime.now() - df[date_col]).dt.days
                    
                    # 2. Status/Stage check
                    status_col = next((c for c in cols if 'stage.name' in c.lower() or 'status' in c.lower()), None)
                    
                    # 3. Display ID (Counting ke liye)
                    id_col = next((c for c in cols if 'display_id' in c or 'id' in c), cols[0])

                    st.subheader("📈 Ticket Pendency Pivot")
                    if status_col:
                        # Pivot Table with Error Handling
                        pivot = df.groupby(status_col).size().reset_index(name='Count')
                        st.table(pivot)
                    else:
                        st.warning("Status column nahi mila. Niche raw data dekhein.")

                    st.subheader("📝 Detailed Data")
                    # Sirf top 10 columns dikhao taaki clutter na ho
                    st.dataframe(df, use_container_width=True)
                    
                    # Download link
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Full CSV", data=csv, file_name="devrev_export.csv")
                else:
                    st.warning("API response empty hai (Works list is empty).")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"System Error: {str(e)}")

# Sidebar
st.sidebar.write(f"Connected to DevRev ✅")
