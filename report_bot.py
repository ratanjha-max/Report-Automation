import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import logging
from typing import Optional, Dict, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
API_ENDPOINT = "https://api.devrev.ai/works.list"
API_TIMEOUT = 10
DEFAULT_LIMIT = 1000
WORK_TYPES = ["ticket", "issue"]
AGING_KEYWORDS = 'MHD|L1|L2|L3|Support|KAM|Payments|Refunds'
AGING_BUCKETS = ["0-1 Day", "2-3 Days", "3+ Days"]

# Streamlit page configuration
st.set_page_config(page_title="UPHD Master Automation", layout="wide")
st.title("🚀 UPHD Full Automation Matrix")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_api_token() -> Optional[str]:
    """Retrieve API token from Streamlit secrets."""
    try:
        return st.secrets["DEVREV_TOKEN"]
    except KeyError:
        st.error("❌ Secrets missing! Please configure 'DEVREV_TOKEN' in Streamlit secrets.")
        st.stop()
        return None

def fetch_works_data(token: str) -> Optional[Dict]:
    """
    Fetch work items from DevRev API.
    
    Args:
        token: DevRev API token
        
    Returns:
        JSON response data or None if request fails
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "limit": DEFAULT_LIMIT,
        "type": WORK_TYPES
    }
    
    try:
        response = requests.get(
            API_ENDPOINT, 
            headers=headers, 
            params=params,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched works data. Status: {response.status_code}")
            return response.json()
        else:
            st.error(f"❌ API Error: {response.status_code}")
            st.write("Response:", response.text)
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error(f"❌ API request timed out after {API_TIMEOUT} seconds.")
        logger.error("API request timeout")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        logger.error(f"Network error: {str(e)}")
        return None

def find_group_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the group column from the dataframe.
    
    Args:
        df: Input dataframe
        
    Returns:
        Group column name or None if not found
    """
    # Try specific column names first
    for col in df.columns:
        if 'group.display_name' in col or 'group.name' in col:
            return col
    
    # Fallback to any column containing 'group'
    for col in df.columns:
        if 'group' in col.lower():
            return col
    
    return None

def find_date_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the date column from the dataframe.
    
    Args:
        df: Input dataframe
        
    Returns:
        Date column name or None if not found
    """
    for col in df.columns:
        if 'created_date' in col.lower():
            return col
    return None

def calculate_aging(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Calculate aging buckets based on creation date.
    
    Args:
        df: Input dataframe
        date_col: Name of the date column
        
    Returns:
        Dataframe with aging calculations
    """
    # Extract date without time component (e.g., remove T18:33:30Z)
    df['Date'] = pd.to_datetime(df[date_col].astype(str).str.split('T').str[0])
    df['Days'] = (pd.Timestamp.now().normalize() - df['Date']).dt.days
    
    def get_bucket(days):
        if days <= 1:
            return "0-1 Day"
        elif days <= 3:
            return "2-3 Days"
        else:
            return "3+ Days"
    
    df['Aging Bucket'] = df['Days'].apply(get_bucket)
    return df

def create_aging_matrix(df: pd.DataFrame, group_col: str) -> Optional[pd.DataFrame]:
    """
    Create pivot table for aging matrix.
    
    Args:
        df: Input dataframe
        group_col: Group column name
        
    Returns:
        Pivot table or None if no matching groups
    """
    # Filter by keywords
    df_filtered = df[df[group_col].str.contains(AGING_KEYWORDS, case=False, na=False)]
    
    if df_filtered.empty:
        return None
    
    # Create pivot table
    pivot = df_filtered.pivot_table(
        index=group_col,
        columns='Aging Bucket',
        values=df_filtered.columns[0],
        aggfunc='count',
        fill_value=0,
        margins=True,
        margins_name='Grand Total'
    )
    
    # Reorder columns
    available_cols = [col for col in AGING_BUCKETS + ['Grand Total'] if col in pivot.columns]
    return pivot[available_cols]

def export_to_csv(df: pd.DataFrame, filename: str) -> bytes:
    """
    Export dataframe to CSV bytes.
    
    Args:
        df: Input dataframe
        filename: Output filename
        
    Returns:
        CSV data as bytes
    """
    return df.to_csv(index=False).encode('utf-8')

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application logic."""
    
    # Sidebar configuration
    st.sidebar.markdown("---")
    st.sidebar.info("📊 Syncing Issues + Tickets at scale.")
    
    # Get API token
    token = get_api_token()
    if not token:
        return
    
    # Main button trigger
    if st.button("▶️ Run Master Sync", use_container_width=True):
        with st.spinner("⏳ Executing Deep Search Query..."):
            # Fetch data from API
            data = fetch_works_data(token)
            if not data:
                return
            
            # Normalize JSON data
            try:
                df = pd.json_normalize(data.get('works', []))
            except Exception as e:
                st.error(f"❌ Error parsing API response: {str(e)}")
                logger.error(f"JSON normalization error: {str(e)}")
                return
            
            if df.empty:
                st.warning("⚠️ API linked but no tickets returned. Check if your token has 'read' permissions for all parts.")
                return
            
            # Find required columns
            group_col = find_group_column(df)
            date_col = find_date_column(df)
            
            if not group_col:
                st.error("❌ Could not identify group column in API response.")
                return
            
            # Clean group column
            df[group_col] = df[group_col].astype(str).fillna('Unassigned')
            
            # Calculate aging if date column exists
            if date_col and date_col in df.columns:
                try:
                    df = calculate_aging(df, date_col)
                except Exception as e:
                    st.warning(f"⚠️ Could not calculate aging: {str(e)}")
                    logger.warning(f"Aging calculation error: {str(e)}")
        
        # Display results
        st.success("✅ Data loaded successfully!")
        
        # Tabs for organized display
        tab1, tab2, tab3 = st.tabs(["📊 Aging Matrix", "📋 Raw Data", "🔍 Debug Info"])
        
        with tab1:
            st.subheader("📌 Aging Matrix (L1, L2, L3, Support)")
            if 'Aging Bucket' in df.columns:
                pivot = create_aging_matrix(df, group_col)
                if pivot is not None:
                    st.dataframe(pivot, use_container_width=True)
                else:
                    st.warning("ℹ️ No matching groups found for the selected keywords.")
            else:
                st.info("ℹ️ Aging data not available for this dataset.")
        
        with tab2:
            st.subheader("📝 All Found Tickets")
            st.dataframe(df, use_container_width=True)
            
            # Export button
            csv_data = export_to_csv(df, "uphd_master_report.csv")
            st.download_button(
                label="📥 Download Master Export (CSV)",
                data=csv_data,
                file_name=f"uphd_master_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with tab3:
            st.subheader("🔍 Debug Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Groups Found:**")
                st.write(df[group_col].unique())
            
            with col2:
                st.write("**Dataset Summary:**")
                st.write(f"- Total Records: {len(df)}")
                st.write(f"- Columns: {len(df.columns)}")
                if 'Aging Bucket' in df.columns:
                    st.write(f"- Aging Buckets: {df['Aging Bucket'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
