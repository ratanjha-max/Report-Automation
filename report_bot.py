import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="UPHD Master Automation", layout="wide")
st.title("🚀 UPHD Full Automation Matrix")

try:
    DEVREV_TOKEN = st.secrets["DEVREV_TOKEN"]
except:
    st.error("Secrets missing!")
    st.stop()

if st.button("Run Master Sync"):
    with st.spinner("Executing Deep Search Query..."):
        # API Endpoint for Searching across all work types
        url = "https://api.devrev.ai/works.list"
        
        # Query Parameters to bypass default filters
        # Hum 'limit=1000' aur 'applies_to_part' (optional) bypass karke sab mang rahe hain
        params = {
            "limit": 1000,
            "type": ["ticket", "issue"] # Dono types cover ho jayenge
        }
        
        headers = {
            "Authorization": f"Bearer {DEVREV_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data.get('works', []))

                if not df.empty:
                    # --- 1. CLEANING COLUMN NAMES ---
                    # DevRev API mein Group aksar 'group.display_name' hota hai
                    group_col = next((c for c in df.columns if 'group.display_name' in c or 'group.name' in c), None)
                    if not group_col:
                        group_col = next((c for c in df.columns if 'group' in c.lower()), None)
                    
                    if group_col:
                        df[group_col] = df[group_col].astype(str).fillna('Unassigned')

                    # --- 2. AGING CALCULATION ---
                    date_col = next((c for c in df.columns if 'created_date' in c.lower()), 'created_date')
                    if date_col in df.columns:
                        # Stripping time like T18:33:30Z
                        df['Date'] = df[date_col].astype(str).str.split('T').str[0]
                        df['Date'] = pd.to_datetime(df['Date'])
                        df['Days'] = (pd.Timestamp.now().normalize() - df['Date']).dt.days
                        
                        def get_bucket(d):
                            if d <= 1: return "0-1 Day"
                            elif d <= 3: return "2-3 Days"
                            else: return "3+ Days"
                        df['Aging Bucket'] = df['Days'].apply(get_bucket)

                    # --- 3. THE SMART MATRIX ---
                    st.subheader("📌 Aging Matrix (L1, L2, L3, Support)")
                    
                    # Flexible Filter: Keywords search in Group names
                    keywords = 'MHD|L1|L2|L3|Support|KAM|Payments|Refunds'
                    df_matrix = df[df[group_col].str.contains(keywords, case=False, na=False)]
                    
                    if not df_matrix.empty:
                        # Pivot Table
                        pivot = df_matrix.pivot_table(
                            index=group_col, 
                            columns='Aging Bucket', 
                            values=df.columns[0], 
                            aggfunc='count', 
                            fill_value=0,
                            margins=True,
                            margins_name='Grand Total'
                        )
                        
                        # Fix column order
                        order = ["0-1 Day", "2-3 Days", "3+ Days", "Grand Total"]
                        valid_order = [o for o in order if o in pivot.columns]
                        st.table(pivot[valid_order])
                    else:
                        st.warning("No matching groups found. All found groups are listed in the sidebar.")

                    # --- 4. DATA EXPORT ---
                    st.subheader("📝 All Found Tickets")
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Master Export", data=csv, file_name="uphd_master_report.csv")
                    
                    # Sidebar Debugging
                    st.sidebar.write("### Debug: Groups Found")
                    st.sidebar.write(df[group_col].unique())

                else:
                    st.warning("API linked but no tickets returned. Check if token has 'read' permissions for all parts.")
            else:
                st.error(f"API Error: {response.status_code}")
                st.write(response.text)
        except Exception as e:
            st.error(f"Code Error: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.info("Syncing Issues + Tickets at scale.")
