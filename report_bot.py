import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="UPHD Aging Matrix", layout="wide")
st.title("📊 UPHD Pendency Aging Matrix")

try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets missing!")
    st.stop()

if st.button("Generate Aging Pivot"):
    with st.spinner("Fetching data from DevRev..."):
        # API URL (Note: added limit=1000 to get more data)
        url = "https://api.devrev.ai/works.list?limit=1000"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.json_normalize(data.get('works', []))

            if not df.empty:
                # --- 1. FIND GROUP COLUMN ---
                group_col = next((c for c in df.columns if 'group' in c.lower() and 'name' in c.lower()), None)
                if not group_col: group_col = next((c for c in df.columns if 'group' in c.lower()), None)

                # --- 2. FLEXIBLE FILTERING ---
                # Ab ye 'MHD' word wale saare groups ko pakad lega (Payments, P&S, Enterprise sab cover honge)
                if group_col:
                    df[group_col] = df[group_col].astype(str).fillna('Unassigned')
                    # Filtering: Groups containing 'MHD' or 'L3'
                    df_filtered = df[df[group_col].str.contains('MHD|L3', case=False, na=False)]
                else:
                    df_filtered = pd.DataFrame()

                if not df_filtered.empty:
                    # --- 3. DATE & AGING ---
                    date_col = next((c for c in df.columns if 'created_date' in c.lower()), 'created_date')
                    if date_col in df_filtered.columns:
                        df_filtered['Date Only'] = df_filtered[date_col].astype(str).str.split('T').str[0]
                        df_filtered['Date Only'] = pd.to_datetime(df_filtered['Date Only'])
                        today = pd.Timestamp.now().normalize()
                        df_filtered['Days'] = (today - df_filtered['Date Only']).dt.days
                        
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df_filtered['Aging Bucket'] = df_filtered['Days'].apply(get_bucket)

                    # --- 4. PIVOT TABLE ---
                    st.subheader("📌 Aging Pivot (MHD & L3 Groups)")
                    pivot = df_filtered.pivot_table(
                        index=group_col, 
                        columns='Aging Bucket', 
                        values=df_filtered.columns[0], 
                        aggfunc='count', 
                        fill_value=0,
                        margins=True,
                        margins_name='Grand Total'
                    )
                    
                    order = ["0-1 Day", "2-3 Days", "3+ Days", "Grand Total"]
                    valid_order = [o for o in order if o in pivot.columns]
                    st.table(pivot[valid_order])

                    st.subheader("📝 Detailed Data View")
                    st.dataframe(df_filtered, use_container_width=True)
                else:
                    st.warning("No MHD/L3 groups found in current tickets.")
            else:
                st.error(f"API Error: {response.status_code}")
        else:
            st.error("Failed to connect.")

st.sidebar.info("Tip: If groups are missing, they might not have active tickets currently.")
