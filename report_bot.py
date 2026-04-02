import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="UPHD Master Matrix", layout="wide")
st.title("🚀 UPHD Full History Aging Matrix")

try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets missing!")
    st.stop()

if st.button("Fetch All Tickets (Including Closed)"):
    with st.spinner("Searching through Closed & Active tickets..."):
        url = "https://api.devrev.ai/works.list"
        headers = {
            "Authorization": f"Bearer {DEVREV_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # --- ULTIMATE FILTER ---
        # Hum specify kar rahe hain ki humein har tarah ka status chahiye
        params = {
            "limit": 1000,
            "type": ["ticket", "issue"],
            "stage.name": ["closed", "resolved", "completed", "in_progress", "open", "staged"]
        }
        
        try:
            # Note: Kuch APIs stages params ko list ki tarah handle karti hain
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # 1. GROUP COLUMN
                    group_col = next((c for c in df.columns if 'group.display_name' in c or 'group.name' in c), None)
                    if not group_col:
                        group_col = next((c for c in df.columns if 'group' in c.lower()), None)
                    
                    if group_col:
                        df[group_col] = df[group_col].astype(str).fillna('Unassigned')

                    # 2. DATE & AGING (Time Strip Logic)
                    date_col = next((c for c in df.columns if 'created_date' in c.lower()), 'created_date')
                    if date_col in df.columns:
                        df['Clean Date'] = df[date_col].astype(str).str.split('T').str[0]
                        df['Clean Date'] = pd.to_datetime(df['Clean Date'])
                        df['Days'] = (pd.Timestamp.now().normalize() - df['Clean Date']).dt.days
                        
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df['Aging Bucket'] = df['Days'].apply(get_bucket)

                    # 3. FILTERING FOR YOUR GROUPS
                    # Ab ye L3 aur KAM Support QR/SB ko pakad lega
                    keywords = 'MHD|KAM|L1|L2|L3|Support'
                    df_filtered = df[df[group_col].str.contains(keywords, case=False, na=False)]

                    if not df_filtered.empty:
                        st.subheader("📌 Aging Pivot (All Statuses)")
                        pivot = df_filtered.pivot_table(
                            index=group_col, 
                            columns='Aging Bucket', 
                            values=df.columns[0], 
                            aggfunc='count', 
                            fill_value=0,
                            margins=True,
                            margins_name='Grand Total'
                        )
                        order = ["0-1 Day", "2-3 Days", "3+ Days", "Grand Total"]
                        valid_order = [o for o in order if o in pivot.columns]
                        st.table(pivot[valid_order])
                    else:
                        st.warning("Filters match nahi huye. Sidebar check karein.")

                    st.subheader("📝 Detailed Data (All Records)")
                    st.dataframe(df, use_container_width=True)
                    
                else:
                    st.warning("API response khali hai. Shayad token permissions issue hai.")
            else:
                st.error(f"API Error {response.status_code}")
        except Exception as e:
            st.error(f"System Error: {str(e)}")

st.sidebar.write("### All Found Groups:")
if 'df' in locals() and group_col in df.columns:
    st.sidebar.write(df[group_col].unique())
