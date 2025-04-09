import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
from datetime import datetime
import time

# === Sidebar UI ===
st.sidebar.title("🔍 SERP Visibility Tracker")
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
brand = st.sidebar.text_input("Brand Name to Track", "")
keywords_input = st.sidebar.text_area("Keywords (one per line)", "")
run = st.sidebar.button("Run Visibility Check")

# === Run the check ===
if run and api_key and keywords_input and brand:
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    results_list = []

    with st.spinner("Running visibility checks..."):
        for keyword in keywords:
            params = {
                "q": keyword,
                "hl": "en",
                "gl": "us",
                "api_key": api_key
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            metadata = results.get("search_metadata", {})

            def scan_json(obj, parent_key="root"):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        new_key = f"{parent_key}.{k}" if parent_key else k
                        if isinstance(v, (dict, list)):
                            scan_json(v, new_key)
                        elif isinstance(v, str) and brand.lower() in v.lower():
                            context = obj.get("category") or obj.get("block_title") or obj.get("title") or k
                            position = obj.get("position", "-")
                            results_list.append({
                                "Keyword": keyword,
                                "SERP Feature": parent_key.split(".")[1] if "." in parent_key else parent_key,
                                "Context": context,
                                "Matched Field": k,
                                "Matched Value": v,
                                "Position": position,
                                "JSON URL": metadata.get("json_endpoint", "-"),
                                "HTML URL": metadata.get("raw_html_file", "-")
                            })
                elif isinstance(obj, list):
                    for item in obj:
                        scan_json(item, parent_key)

            scan_json(results)
            time.sleep(1.2)

    if results_list:
        df = pd.DataFrame(results_list)
        st.success("✅ Brand visibility matches found:")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"visibility_{brand}_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime='text/csv'
        )
    else:
        st.warning("No brand mentions found in SERP features.")
