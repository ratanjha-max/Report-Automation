import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="DevRev UPHD Automator", layout="wide")
st.title("📊 DevRev Reporting Automation")

# Fetch Token from Secrets
try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Tijori khali hai! Please add 'DEVREV_TOKEN' in Streamlit Secrets.")
    st.stop()

if st.button("Sync Live Data from DevRev"):
    with st.spinner("Fetching data from CRM..."):
        url = "https://api.devrev.ai/works.list"
        headers = {"Authorization": f"Bearer {DEVREV_TOKEN}", "Content-Type": "application/json"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Normalize nested data from DevRev
            df = pd.json_normalize(data.get('works', []))

            if not df.empty:
                # --- COLUMN MAPPING ---
                # DevRev API names ko aapke Excel titles se match kar raha hoon
                mapping = {
                    'title': 'Title',
                    'stage.name': 'Stage',
                    'owner.display_name': 'Owner',
                    'created_date': 'Created date',
                    'custom_fields.rev_merchant_id': 'Merchant ID', # Common DevRev field
                    'custom_fields.issue_category_l1': 'Issue category L1'
                }
                
                # Check actual available columns to prevent errors
                actual_cols = df.columns.tolist()
                
                # 1. PENDENCY CALCULATION (Created Date)
                # API usually returns 'created_date'
                if 'created_date' in actual_cols:
                    df['created_date'] = pd.to_datetime(df['created_date'])
                    df['Pendency (Days)'] = (datetime.now() - df['created_date']).dt.days
                
                # 2. PIVOT TABLE (By Stage/Status)
                st.subheader("📈 Stage-wise Pendency Pivot")
                
                # Find the right 'Stage' column
                status_col = 'stage.name' if 'stage.name' in actual_cols else 'status'
                
                if status_col in actual_cols:
                    pivot = df.pivot_table(
                        index=status_col, 
                        values='display_id', 
                        aggfunc='count', 
                        fill_value=0
                    )
                    st.dataframe(pivot, use_container_width=True)
                else:
                    st.warning("Could not find 'Stage' column for Pivot. Check raw data below.")

                # 3. FULL REPORT VIEW
                st.subheader("📝 Detailed Report")
                # Showing only relevant columns if they exist
                cols_to_show = [c for c in ['display_id', 'title', 'stage.name', 'owner.display_name', 'Pendency (Days)'] if c in actual_cols]
                st.write(df[cols_to_show] if cols_to_show else df)

                # 4. DOWNLOAD BUTTON
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Full Report (CSV)", data=csv, file_name="uphd_pendency_report.csv")

            else:
                st.warning("No tickets found in the DevRev response.")
        else:
            st.error(f"API Error {response.status_code}: {response.text}")

# Sidebar Info
st.sidebar.info(f"Connected as: {DEVREV_TOKEN[:10]}...")
st.sidebar.write("Last Sync: " + datetime.now().strftime("%H:%M:%S"))
