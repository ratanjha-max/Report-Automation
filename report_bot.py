import streamlit as st
import pandas as pd
import requests
from datetime import datetime

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
                    cols = df.columns.tolist()
                    
                    # --- FIX: REMOVE TIME (T18:33:30Z) AS PER YOUR HINT ---
                    date_col = next((c for c in cols if 'created_date' in c.lower()), None)
                    if date_col:
                        # Step 1: Force to String and split at 'T' to get only Date (YYYY-MM-DD)
                        df[date_col] = df[date_col].astype(str).str.split('T').str[0]
                        
                        # Step 2: Convert the clean date string to datetime
                        df[date_col] = pd.to_datetime(df[date_col])
                        
                        # Step 3: Get today's date without time for calculation
                        today = pd.Timestamp.now().normalize()
                        
                        # Step 4: Calculate Days
                        df['Days'] = (today - df[date_col]).dt.days
                        
                        # Define Buckets
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df['Aging Bucket'] = df['Days'].apply(get_bucket)

                    # --- PIVOT LOGIC ---
                    group_col = next((c for c in cols if 'group' in c.lower()), None)
                    if group_col:
                        # Grouping by your specified groups
                        pivot = df.pivot_table(
                            index=group_col, 
                            columns='Aging Bucket', 
                            values='display_id', 
                            aggfunc='count', 
                            fill_value=0,
                            margins=True,
                            margins_name='Grand Total'
                        )
                        
                        # Sorting Buckets
                        bucket_order = ["0-1 Day", "2-3 Days", "3+ Days", "Grand Total"]
                        available_cols = [b for b in bucket_order if b in pivot.columns]
                        st.table(pivot[available_cols])
                    
                    st.subheader("📝 Detailed View")
                    st.dataframe(df, use_container_width=True)
                    
                else:
                    st.warning("No data found.")
            else:
                st.error(f"API Error {response.status_code}")
        except Exception as e:
            st.error(f"System Error: {str(e)}")

st.sidebar.write("Time Filter: Date Only (Time Stripped) ✅")
