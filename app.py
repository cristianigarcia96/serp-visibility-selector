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

            # Loop through top-level SERP features only
            for block, content in results.items():
                if block in ["ads", "organic_results", "related_searches", "immersive_products", "inline_videos", "discussions_and_forums", "local_results", "shopping_results", "top_stories", "knowledge_graph", "video_results", "image_results", "people_also_ask"]:
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                item_text = " ".join([str(v) for v in item.values() if isinstance(v, str)])
                                if brand.lower() in item_text.lower():
                                    position = item.get("position", "-")
                                    context = next((v for v in item.values() if isinstance(v, str) and brand.lower() in v.lower()), "-")

                                    match_id = (keyword, block, context)
                                    if match_id not in seen_matches:
                                        seen_matches.add(match_id)
                                        results_list.append({
                                            "Keyword": keyword,
                                            "SERP Feature": block,
                                            "Context": context,
                                            "Position": position,
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
