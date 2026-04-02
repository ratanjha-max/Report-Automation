import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="UPHD Master Matrix", layout="wide")
st.title("🚀 UPHD Ultimate Data Sync")

try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets missing!")
    st.stop()

if st.button("Force Sync All MHD/KAM Data"):
    with st.spinner("Searching specifically for KAM & MHD groups..."):
        # API Endpoint
        url = "https://api.devrev.ai/works.list"
        headers = {
            "Authorization": f"Bearer {DEVREV_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # --- TARGETED SEARCH PARAMS ---
        # Hum specifically 'ticket' mang rahe hain aur limit 1000 kar rahe hain
        params = {
            "limit": 1000,
            "type": ["ticket", "issue"],
            # Saare possible stages mang rahe hain taaki closed/resolved bhi aa jayein
            "stage.name": ["closed", "resolved", "completed", "in_progress", "open", "staged", "backlog"]
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # 1. GROUP COLUMN FINDER
                    group_col = next((c for c in df.columns if 'group.display_name' in c or 'group.name' in c), None)
                    if not group_col:
                        group_col = next((c for c in df.columns if 'group' in c.lower()), None)
                    
                    if group_col:
                        df[group_col] = df[group_col].astype(str).fillna('Unassigned')

                        # --- 2. BROAD KEYWORD FILTERING ---
                        # Ye 'KAM', 'MHD', 'L1', 'L2', 'L3' sabko capture karega
                        keywords = 'KAM|MHD|L1|L2|L3|Support'
                        df_filtered = df[df[group_col].str.contains(keywords, case=False, na=False)]
                        
                        if not df_filtered.empty:
                            # AGING CALCULATION
                            date_col = next((c for c in df.columns if 'created_date' in c.lower()), 'created_date')
                            if date_col in df_filtered.columns:
                                df_filtered['Date'] = df_filtered[date_col].astype(str).str.split('T').str[0]
                                df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
                                df_filtered['Aging'] = (pd.Timestamp.now().normalize() - df_filtered['Date']).dt.days
                                
                                def get_bucket(d):
                                    if d <= 1: return "0-1 Day"
                                    elif d <= 3: return "2-3 Days"
                                    else: return "3+ Days"
                                df_filtered['Aging Bucket'] = df_filtered['Aging'].apply(get_bucket)

                            st.subheader("📌 Aging Pivot Table")
                            pivot = df_filtered.pivot_table(
                                index=group_col, 
                                columns='Aging Bucket', 
                                values=df.columns[0], 
                                aggfunc='count', 
                                fill_value=0,
                                margins=True,
                                margins_name='Grand Total'
                            )
                            st.table(pivot)
                            
                            st.subheader("📝 Detailed Data (Filtered)")
                            st.dataframe(df_filtered, use_container_width=True)
                        else:
                            st.warning("Specified groups not found in the first 1000 records.")
                            st.info(f"Available Groups in API: {df[group_col].unique().tolist()}")
                    
                else:
                    st.warning("No data returned from API.")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.sidebar.write("Checking: All Statuses + 1000 Records ✅")
