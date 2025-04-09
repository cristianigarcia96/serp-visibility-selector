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

# === Feature labeling overrides ===
feature_map = {
    "related_searches": "Related searches",
    "knowledge_graph": "Knowledge panel",
    "organic_results": "Organic results",
    "inline_videos": "Videos",
    "ads": "Ads",
    "shopping_results": "Shopping results"
}

if run and api_key and keywords_input and brand:
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    summary_results = []
    seen = set()

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

            matches = {}

            def recursive_search(data, path=""):
                if isinstance(data, dict):
                    for k, v in data.items():
                        new_path = f"{path}::{k}" if path else k

                        # For immersive_products, use category if available
                        if k == "immersive_products" and isinstance(v, list):
                            for i, item in enumerate(v):
                                category = item.get("category", "immersive_products")
                                new_feature_name = f"{k}::{category}"
                                for sub_k, sub_v in item.items():
                                    sub_path = f"{new_path}[{i}]::{sub_k}"
                                    if isinstance(sub_v, str) and brand.lower() in sub_v.lower():
                                        yield (new_feature_name, sub_v, i + 1)
                        elif isinstance(v, (dict, list)):
                            yield from recursive_search(v, new_path)
                        elif isinstance(v, str) and brand.lower() in v.lower():
                            yield (new_path, v, None)
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        new_path = f"{path}[{i}]"
                        yield from recursive_search(item, new_path)

            for path, value, index in recursive_search(results):
                path_parts = [p.split("[")[0] for p in path.split("::") if not p.endswith("[]")]
                feature_key = next((p for p in path_parts if p in feature_map or p.startswith("immersive_products")), path_parts[0] if path_parts else "other")
                feature_name = feature_map.get(feature_key, feature_key)

                position = index if index is not None else "-"
                match_key = (keyword, feature_name)

                if match_key not in matches:
                    matches[match_key] = {
                        "Keyword": keyword,
                        "SERP Feature": feature_name,
                        "Mentions": 1,
                        "Top Position": position,
                        "JSON URL": metadata.get("json_endpoint", "-"),
                        "HTML URL": metadata.get("raw_html_file", "-")
                    }
                else:
                    matches[match_key]["Mentions"] += 1
                    if position != "-" and (matches[match_key]["Top Position"] == "-" or position < matches[match_key]["Top Position"]):
                        matches[match_key]["Top Position"] = position

            summary_results.extend(matches.values())
            time.sleep(1.2)

    if summary_results:
        df = pd.DataFrame(summary_results)
        st.success("✅ Brand visibility summary:")
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
