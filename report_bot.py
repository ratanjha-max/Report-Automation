import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

st.set_page_config(page_title="UPHD Aging Matrix", layout="wide")
st.title("📊 UPHD Pendency Aging Matrix")

# Token fetch from Secrets
try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets mein 'DEVREV_TOKEN' nahi mila!")
    st.stop()

if st.button("Generate Aging Pivot"):
    with st.spinner("Fetching and Calculating..."):
        url = "https://api.devrev.ai/works.list"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # 1. DATE & AGING CALCULATION
                    date_col = next((c for c in df.columns if 'created_date' in c.lower()), None)
                    if date_col:
                        df[date_col] = pd.to_datetime(df[date_col], utc=True)
                        now_utc = datetime.now(timezone.utc)
                        df['Days'] = (now_utc - df[date_col]).dt.days
                        
                        # Define Buckets (Exactly like your screenshot)
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df['Aging Bucket'] = df['Days'].apply(get_bucket)

                    # 2. GROUP FILTERING
                    # API mein Group column ka naam dhundna
                    group_col = next((c for c in df.columns if 'group' in c.lower()), None)
                    
                    if group_col:
                        # Sirf relevant groups rakhein (Modify names if they differ in API)
                        target_groups = ['UPHD-PAYMENTS', 'UPHD-REFUNDS', 'L3-SUPPORT', 'KAM-TEAM'] 
                        df_filtered = df[df[group_col].str.contains('|'.join(target_groups), na=False, case=False)]
                    else:
                        df_filtered = df

                    # 3. GENERATE PIVOT (The Aging Matrix)
                    st.subheader("📌 Aging Pivot Table")
                    
                    # Columns define karna for sorting
                    bucket_order = ["0-1 Day", "2-3 Days", "3+ Days"]
                    
                    if group_col:
                        pivot = df_filtered.pivot_table(
                            index=group_col, 
                            columns='Aging Bucket', 
                            values='display_id', 
                            aggfunc='count', 
                            fill_value=0,
                            margins=True, # For Total column
                            margins_name='Grand Total'
                        )
                        
                        # Sort columns properly
                        available_buckets = [b for b in bucket_order if b in pivot.columns]
                        if 'Grand Total' in pivot.columns: available_buckets.append('Grand Total')
                        pivot = pivot[available_buckets]
                        
                        st.table(pivot)
                    
                    st.subheader("📝 Detailed View")
                    st.dataframe(df_filtered[['display_id', group_col, 'Aging Bucket', 'Days']] if group_col in df_filtered.columns else df_filtered)
                    
                else:
                    st.warning("No data found in DevRev.")
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.write("Logic: Created Date vs Today (UTC)")
