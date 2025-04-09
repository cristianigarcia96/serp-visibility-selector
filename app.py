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
    seen_matches = set()

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

            def search_dict(d, path=""):
                if isinstance(d, dict):
                    for k, v in d.items():
                        new_path = f"{path}::{k}" if path else k
                        if isinstance(v, (dict, list)):
                            yield from search_dict(v, new_path)
                        elif isinstance(v, str) and brand.lower() in v.lower():
                            yield (new_path, v)
                elif isinstance(d, list):
                    for i, item in enumerate(d):
                        new_path = f"{path}[{i}]"
                        yield from search_dict(item, new_path)

            seen_features = set()

            for path, value in search_dict(results):
                # find the feature name from path, last 1-2 tokens
                feature_parts = [p for p in path.split("::") if not p.startswith("[")]
                feature = feature_parts[-1] if feature_parts else path
                context = value.strip()[:200]  # Trim long text
                match_id = (keyword, feature, context)
                if match_id not in seen_matches:
                    seen_matches.add(match_id)
                    results_list.append({
                        "Keyword": keyword,
                        "SERP Feature": feature,
                        "Context": context,
                        "Position": "-",
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
