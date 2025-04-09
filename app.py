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

            for key, value in results.items():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for field, field_value in item.items():
                                if isinstance(field_value, str) and brand.lower() in field_value.lower():
                                    context = item.get("category") or item.get("block_title") or item.get("title") or key
                                    position = item.get("position", "-")
                                    results_list.append({
                                        "Keyword": keyword,
                                        "SERP Feature": key,
                                        "Context": context,
                                        "Matched Field": field,
                                        "Matched Value": field_value,
                                        "Position": position,
                                        "JSON URL": metadata.get("json_endpoint", "-"),
                                        "HTML URL": metadata.get("raw_html_file", "-")
                                    })
                elif isinstance(value, dict):
                    for field, field_value in value.items():
                        if isinstance(field_value, str) and brand.lower() in field_value.lower():
                            results_list.append({
                                "Keyword": keyword,
                                "SERP Feature": key,
                                "Context": key,
                                "Matched Field": field,
                                "Matched Value": field_value,
                                "Position": value.get("position", "-"),
                                "JSON URL": metadata.get("json_endpoint", "-"),
                                "HTML URL": metadata.get("raw_html_file", "-")
                            })

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
