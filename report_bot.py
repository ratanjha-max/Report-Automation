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
    with st.spinner("Fetching from DevRev..."):
        # API URL
        url = "https://api.devrev.ai/works.list"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Flattening the JSON
            df = pd.json_normalize(data.get('works', []))

            if not df.empty:
                # --- 1. DYNAMICALLY FIND GROUP COLUMN ---
                # Kabhi-kabhi API 'group.display_name' bhejti hai
                group_col = next((c for c in df.columns if 'group' in c.lower() and 'name' in c.lower()), None)
                if not group_col:
                    group_col = next((c for c in df.columns if 'group' in c.lower()), None)

                # --- 2. FILTERING LOGIC (STRICT GROUPS) ---
                target_groups = [
                    'MHD KAM Support QR/SB', 
                    'MHD P&S L3 Agent', 
                    'MHD Payments L3 Agent', 
                    'MHD Profile L3 Agent'
                ]
                
                if group_col:
                    # Clean the data: remove extra spaces and make it case-insensitive for matching
                    df[group_col] = df[group_col].astype(str).str.strip()
                    df_filtered = df[df[group_col].str.contains('|'.join(target_groups), case=False, na=False)]
                else:
                    df_filtered = pd.DataFrame() # Empty if no group col found

                if not df_filtered.empty:
                    # --- 3. DATE & AGING CALCULATION ---
                    date_col = next((c for c in df.columns if 'created_date' in c.lower()), 'created_date')
                    if date_col in df_filtered.columns:
                        df_filtered['Created date clean'] = df_filtered[date_col].astype(str).str.split('T').str[0]
                        df_filtered['Created date clean'] = pd.to_datetime(df_filtered['Created date clean'])
                        today = pd.Timestamp.now().normalize()
                        df_filtered['Days'] = (today - df_filtered['Created date clean']).dt.days
                        
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df_filtered['Aging Bucket'] = df_filtered['Days'].apply(get_bucket)

                    # --- 4. PIVOT TABLE ---
                    st.subheader("📌 Aging Pivot")
                    # Using 'display_id' or first column for count
                    count_col = 'display_id' if 'display_id' in df_filtered.columns else df_filtered.columns[0]
                    
                    pivot = df_filtered.pivot_table(
                        index=group_col, 
                        columns='Aging Bucket', 
                        values=count_col, 
                        aggfunc='count', 
                        fill_value=0,
                        margins=True,
                        margins_name='Grand Total'
                    )
                    
                    order = ["0-1 Day", "2-3 Days", "3+ Days", "Grand Total"]
                    valid_order = [o for o in order if o in pivot.columns]
                    st.table(pivot[valid_order])

                    st.subheader("📝 Detailed Data")
                    st.dataframe(df_filtered, use_container_width=True)
                else:
                    st.warning("⚠️ No data found for the specified Groups.")
                    st.info(f"Available Groups in API: {df[group_col].unique().tolist() if group_col else 'None'}")
            else:
                st.error(f"API Error: {response.status_code}")
        else:
            st.error("Failed to connect to DevRev.")

st.sidebar.write("Filter: Strict Case-Insensitive ✅")
