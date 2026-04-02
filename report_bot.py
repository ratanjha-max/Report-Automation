import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- SECURITY: AUTHENTICATION ---
# Paste your Token here or use Streamlit Secrets for safety
DEVREV_TOKEN = "eyJhbGciOiJSUzI1NiIsImlzcyI6Imh0dHBzOi8vYXV0aC10b2tlbi5kZXZyZXYuYWkvIiwia2lkIjoic3RzX2tpZF9yc2EiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiamFudXMiXSwiYXpwIjoiZG9uOmlkZW50aXR5OmR2cnYtaW4tMTpkZXZvLzJHMlZacWNyaWk6ZGV2dS8xMTcyIiwiZXhwIjoxNzc3NzM4NTAyLCJodHRwOi8vZGV2cmV2LmFpL2F1dGgwX3VpZCI6ImRvbjppZGVudGl0eTpkdnJ2LXVzLTE6ZGV2by9zdXBlcjphdXRoMF91c2VyL29pZGN8cGFzc3dvcmRsZXNzfGVtYWlsfDY4YzEwYjJkN2YwNmYzM2U2NDk0MjEyZiIsImh0dHA6Ly9kZXZyZXYuYWkvYXV0aDBfdXNlcl9pZCI6Im9pZGN8cGFzc3dvcmRsZXNzfGVtYWlsfDY4YzEwYjJkN2YwNmYzM2U2NDk0MjEyZiIsImh0dHA6Ly9kZXZyZXYuYWkvZGV2b19kb24iOiJkb246aWRlbnRpdHk6ZHZydi1pbi0xOmRldm8vMkcyVlpxY3JpaSIsImh0dHA6Ly9kZXZyZXYuYWkvZGV2b2lkIjoiREVWLTJHMlZacWNyaWkiLCJodHRwOi8vZGV2cmV2LmFpL2RldnVpZCI6IkRFVlUtMTE3MiIsImh0dHA6Ly9kZXZyZXYuYWkvZGlzcGxheW5hbWUiOiJSYXRhbiBLdW1hciBKaGEiLCJodHRwOi8vZGV2cmV2LmFpL2VtYWlsIjoicmF0YW4uamhhQHBheXRtLmNvbSIsImh0dHA6Ly9kZXZyZXYuYWkvZnVsbG5hbWUiOiJSYXRhbiBLdW1hciBKaGEiLCJodHRwOi8vZGV2cmV2LmFpL2lzX3ZlcmlmaWVkIjp0cnVlLCJodHRwOi8vZGV2cmV2LmFpL3Rva2VudHlwZSI6InVybjpkZXZyZXY6cGFyYW1zOm9hdXRoOnRva2VuLXR5cGU6cGF0IiwiaWF0IjoxNzc1MTQ2NTAyLCJpc3MiOiJodHRwczovL2F1dGgtdG9rZW4uZGV2cmV2LmFpLyIsImp0aSI6ImRvbjppZGVudGl0eTpkdnJ2LWluLTE6ZGV2by8yRzJWWnFjcmlpOnRva2VuLzFIYXhrY05laCIsIm9yZ19pZCI6Im9yZ19EcktKVVB1NzYwanVTQVR2Iiwic3ViIjoiZG9uOmlkZW50aXR5OmR2cnYtaW4tMTpkZXZvLzJHMlZacWNyaWk6ZGV2dS8xMTcyIn0.v6r-_D33Om8CF1IyuSelYSLMKOKXTPiOva-8WoyfoKOFnofKGL7CvZZiFy_1HZkh05Sf40J3b8t7wdNpKj0cMLlnUCfyw9hFjBmRYF6Cr_4P-B4tBsZt-pg4LpWBbFn5eilVqlZbEMtctsSAv3jzgS0DL8RjyTFzmkHndHRTDSjZeX2e2qS5anvmWbUtgpFcQYXKjRwpJ5PWtaYCmXpVJDz6JqZAjuMdYTy6qOCaOOOZxAByncZBHSgJtOq8T88RNJEvjyrbSZ98drFyZXTfbmoHHgi_1wvLPCVzAvIBBI4L5Msz2_HtlguW7YA6316oYmmRja9s5h3YC_W8pFyB5Q" 

st.title("🚀 DevRev Automated Pendency Report")

if st.button("Fetch & Sync Live Data"):
    with st.spinner("Connecting to DevRev API..."):
        
        # API Configuration
        url = "https://api.devrev.ai/works.list" # Example endpoint for tickets
        headers = {
            "Authorization": f"Bearer {eyJhbGciOiJSUzI1NiIsImlzcyI6Imh0dHBzOi8vYXV0aC10b2tlbi5kZXZyZXYuYWkvIiwia2lkIjoic3RzX2tpZF9yc2EiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiamFudXMiXSwiYXpwIjoiZG9uOmlkZW50aXR5OmR2cnYtaW4tMTpkZXZvLzJHMlZacWNyaWk6ZGV2dS8xMTcyIiwiZXhwIjoxNzc3NzM4NTAyLCJodHRwOi8vZGV2cmV2LmFpL2F1dGgwX3VpZCI6ImRvbjppZGVudGl0eTpkdnJ2LXVzLTE6ZGV2by9zdXBlcjphdXRoMF91c2VyL29pZGN8cGFzc3dvcmRsZXNzfGVtYWlsfDY4YzEwYjJkN2YwNmYzM2U2NDk0MjEyZiIsImh0dHA6Ly9kZXZyZXYuYWkvYXV0aDBfdXNlcl9pZCI6Im9pZGN8cGFzc3dvcmRsZXNzfGVtYWlsfDY4YzEwYjJkN2YwNmYzM2U2NDk0MjEyZiIsImh0dHA6Ly9kZXZyZXYuYWkvZGV2b19kb24iOiJkb246aWRlbnRpdHk6ZHZydi1pbi0xOmRldm8vMkcyVlpxY3JpaSIsImh0dHA6Ly9kZXZyZXYuYWkvZGV2b2lkIjoiREVWLTJHMlZacWNyaWkiLCJodHRwOi8vZGV2cmV2LmFpL2RldnVpZCI6IkRFVlUtMTE3MiIsImh0dHA6Ly9kZXZyZXYuYWkvZGlzcGxheW5hbWUiOiJSYXRhbiBLdW1hciBKaGEiLCJodHRwOi8vZGV2cmV2LmFpL2VtYWlsIjoicmF0YW4uamhhQHBheXRtLmNvbSIsImh0dHA6Ly9kZXZyZXYuYWkvZnVsbG5hbWUiOiJSYXRhbiBLdW1hciBKaGEiLCJodHRwOi8vZGV2cmV2LmFpL2lzX3ZlcmlmaWVkIjp0cnVlLCJodHRwOi8vZGV2cmV2LmFpL3Rva2VudHlwZSI6InVybjpkZXZyZXY6cGFyYW1zOm9hdXRoOnRva2VuLXR5cGU6cGF0IiwiaWF0IjoxNzc1MTQ2NTAyLCJpc3MiOiJodHRwczovL2F1dGgtdG9rZW4uZGV2cmV2LmFpLyIsImp0aSI6ImRvbjppZGVudGl0eTpkdnJ2LWluLTE6ZGV2by8yRzJWWnFjcmlpOnRva2VuLzFIYXhrY05laCIsIm9yZ19pZCI6Im9yZ19EcktKVVB1NzYwanVTQVR2Iiwic3ViIjoiZG9uOmlkZW50aXR5OmR2cnYtaW4tMTpkZXZvLzJHMlZacWNyaWk6ZGV2dS8xMTcyIn0.v6r-_D33Om8CF1IyuSelYSLMKOKXTPiOva-8WoyfoKOFnofKGL7CvZZiFy_1HZkh05Sf40J3b8t7wdNpKj0cMLlnUCfyw9hFjBmRYF6Cr_4P-B4tBsZt-pg4LpWBbFn5eilVqlZbEMtctsSAv3jzgS0DL8RjyTFzmkHndHRTDSjZeX2e2qS5anvmWbUtgpFcQYXKjRwpJ5PWtaYCmXpVJDz6JqZAjuMdYTy6qOCaOOOZxAByncZBHSgJtOq8T88RNJEvjyrbSZ98drFyZXTfbmoHHgi_1wvLPCVzAvIBBI4L5Msz2_HtlguW7YA6316oYmmRja9s5h3YC_W8pFyB5Q}",
            "Content-Type": "application/json"
        }
        
        # Calling the API
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Convert JSON to Pandas DataFrame
            # Note: 'works' is a common key in DevRev, adjust based on actual JSON structure
            df = pd.json_normalize(data['works']) 
            
            # --- PENDENCY CALCULATION ---
            # Replace 'created_date' with the exact column name from DevRev
            df['created_date'] = pd.to_datetime(df['created_date'])
            today = datetime.now()
            df['Pendency (Days)'] = (today - df['created_date']).dt.days
            
            # --- PIVOT TABLE ---
            pivot_table = df.pivot_table(
                index='status', 
                values='display_id', 
                aggfunc='count', 
                fill_value=0
            )
            
            st.success("Data Synced Successfully!")
            st.write("### Live Pendency Pivot", pivot_table)
            
            # Download Option
            st.download_button("Export to Excel", data=df.to_csv(), file_name="devrev_sync.csv")
            
        else:
            st.error(f"Failed to connect. Error Code: {response.status_code}")
            st.write(response.text)