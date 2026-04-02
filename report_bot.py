import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="UPHD Aging Matrix", layout="wide")
st.title("📊 UPHD Pendency Aging Matrix")

# Token from Secrets
try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets mein 'DEVREV_TOKEN' nahi mila!")
    st.stop()

if st.button("Generate Aging Pivot"):
    with st.spinner("Processing DevRev Data..."):
        url = "https://api.devrev.ai/works.list"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # --- 1. COLUMN NAME CLEANING & MAPPING ---
                    # DevRev API names often use dots (e.g., stage.name). 
                    # We map them to your exact required names.
                    mapping = {
                        'display_id': 'Items',
                        'title': 'Title',
                        'stage.name': 'Stage',
                        'owner.display_name': 'Owner',
                        'created_date': 'Created date',
                        'modified_date': 'Modified date',
                        'group.name': 'Group',
                        'custom_fields.issue_category_l1': 'Issue category L1',
                        'custom_fields.issue_category_l2': 'Issue category L2',
                        'custom_fields.issue_category_l3': 'Issue category L3',
                        'custom_fields.rev_merchant_id': 'Merchant ID',
                        'custom_fields.department_list': 'Department List',
                        'custom_fields.pwod_reason': 'PWOD Reason',
                        'source.type': 'Source'
                    }
                    df.rename(columns=mapping, inplace=True)

                    # --- 2. FILTER SPECIFIC GROUPS ---
                    target_groups = [
                        'MHD KAM Support QR/SB', 
                        'MHD P&S L3 Agent', 
                        'MHD Payments L3 Agent', 
                        'MHD Profile L3 Agent'
                    ]
                    
                    # Agar column 'Group' hai toh filter karo
                    if 'Group' in df.columns:
                        df = df[df['Group'].isin(target_groups)]
                    else:
                        st.error("API response mein 'Group' column nahi mila. Check raw data.")
                        st.stop()

                    # --- 3. DATE & AGING CALCULATION (Cleaned format) ---
                    if 'Created date' in df.columns:
                        # Stripping time (T18:33:30Z) as per your hint
                        df['Created date clean'] = df['Created date'].astype(str).str.split('T').str[0]
                        df['Created date clean'] = pd.to_datetime(df['Created date clean'])
                        today = pd.Timestamp.now().normalize()
                        df['Days'] = (today - df['Created date clean']).dt.days
                        
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df['Aging Bucket'] = df['Days'].apply(get_bucket)

                    # --- 4. GENERATE PIVOT ---
                    st.subheader("📌 Aging Pivot (Filtered Groups)")
                    pivot = df.pivot_table(
                        index='Group', 
                        columns='Aging Bucket', 
                        values='Items', 
                        aggfunc='count', 
                        fill_value=0,
                        margins=True,
                        margins_name='Grand Total'
                    )
                    
                    bucket_order = ["0-1 Day", "2-3 Days", "3+ Days", "Grand Total"]
                    available_cols = [b for b in bucket_order if b in pivot.columns]
                    st.table(pivot[available_cols])

                    # --- 5. SELECT ONLY REQUIRED COLUMNS FOR VIEW ---
                    required_cols = [
                        'Title', 'Items', 'Stage', 'Owner', 'Created date', 
                        'Modified date', 'Group', 'Issue category L1', 
                        'Issue category L2', 'Issue category L3', 'Merchant ID', 
                        'Department List', 'PWOD Reason', 'Source'
                    ]
                    # Only keep columns that exist in the dataframe
                    final_view_cols = [c for c in required_cols if c in df.columns]
                    
                    st.subheader("📝 Detailed Data (Strict Columns)")
                    st.dataframe(df[final_view_cols], use_container_width=True)

                else:
                    st.warning("No data found.")
            else:
                st.error(f"API Error {response.status_code}")
        except Exception as e:
            st.error(f"System Error: {str(e)}")

st.sidebar.write("Filters: Strict Group & Columns ✅")
