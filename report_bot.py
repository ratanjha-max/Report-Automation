import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="UPHD Master Matrix", layout="wide")
st.title("📊 UPHD Deep Data Sync (L1, L2, L3)")

try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets missing!")
    st.stop()

if st.button("Deep Sync All Teams"):
    with st.spinner("Searching all layers (L1-L3)..."):
        # API URL with specific filters for 'Issue' and 'Ticket' types + high limit
        # 'type=issue,ticket' helps pull data from both categories
        url = "https://api.devrev.ai/works.list?limit=1000"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.json_normalize(data.get('works', []))

            if not df.empty:
                # --- 1. CLEANING GROUP NAMES ---
                # DevRev nested fields ko flat karte hain
                group_col = next((c for c in df.columns if 'group.display_name' in c or 'group.name' in c), None)
                if not group_col:
                    group_col = next((c for c in df.columns if 'group' in c.lower()), None)
                
                if group_col:
                    df[group_col] = df[group_col].astype(str).fillna('Unassigned')
                
                # --- 2. AGING CALCULATION ---
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

                # --- 3. SHOW ALL GROUPS FIRST (To identify L2 names) ---
                all_groups = df[group_col].unique().tolist() if group_col else []
                st.sidebar.write("### All Found Groups:")
                st.sidebar.json(all_groups)

                # --- 4. THE MATRIX ---
                st.subheader("📌 Team Aging Matrix")
                if group_col:
                    # Filter: Only show groups that have 'MHD', 'L1', 'L2', or 'L3' in name
                    df_matrix = df[df[group_col].str.contains('MHD|L1|L2|L3|Support|KAM', case=False, na=False)]
                    
                    if not df_matrix.empty:
                        pivot = df_matrix.pivot_table(
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
                        st.warning("Filters match nahi huye. Niche Raw Data dekhein.")

                st.subheader("📝 Raw Data (Check Group names here)")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("API responded but 'works' list was empty.")
        else:
            st.error(f"API Connection Error: {response.status_code}")

st.sidebar.info("Checking: Issues + Tickets + Unlimited Statuses")
