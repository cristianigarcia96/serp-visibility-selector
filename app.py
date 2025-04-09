import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="SERP Visibility Tracker", layout="wide")

# === Sidebar UI ===
st.sidebar.title("🔍 SERP Visibility Tracker")
st.sidebar.markdown("Track your brand's visibility across Google SERP features.")

api_key = st.sidebar.text_input("🔐 SerpAPI Key", type="password")
brand = st.sidebar.text_input("🏷️ Brand Name to Track")
keywords_input = st.sidebar.text_area("📝 Keywords (one per line)")
run = st.sidebar.button("🚀 Run Visibility Check")

# === Feature labeling overrides ===
feature_map = {
    "related_searches": "Related searches",
    "knowledge_graph": "Knowledge panel",
    "organic_results": "Organic results",
    "inline_videos": "Videos",
    "ads": "Ads",
    "shopping_results": "Shopping results"
}

st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
        }
        .stDataFrame thead tr th {
            background-color: #f4f4f4;
        }
        .stDownloadButton button {
            background-color: #4CAF50;
            color: white;
        }
        .stButton button {
            background-color: #1f77b4;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

if run and api_key and keywords_input and brand:
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    summary_results = []

    with st.spinner("🔍 Running visibility checks across keywords..."):
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

            serp_mentions = {}

            # === Organic Results with Position ===
            for item in results.get("organic_results", []):
                position = item.get("position")
                if brand.lower() in str(item).lower():
                    key = (keyword, "Organic results")
                    serp_mentions.setdefault(key, []).append(position)

            # === Other Features ===
            def search_features(data, path=""):
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k == "organic_results":
                            continue  # already handled above

                        new_path = f"{path}::{k}" if path else k

                        if k == "immersive_products" and isinstance(v, list):
                            for item in v:
                                category = item.get("category", "immersive_products")
                                if brand.lower() in str(item).lower():
                                    key = (keyword, category)
                                    serp_mentions.setdefault(key, []).append(None)

                        elif isinstance(v, (dict, list)):
                            search_features(v, new_path)
                        elif isinstance(v, str) and brand.lower() in v.lower():
                            label_key = next((p for p in path.split("::") if p in feature_map), path.split("::")[-1])
                            feature_name = feature_map.get(label_key, label_key)
                            key = (keyword, feature_name)
                            serp_mentions.setdefault(key, []).append(None)

                elif isinstance(data, list):
                    for item in data:
                        search_features(item, path)

            search_features(results)

            for (kw, feature), positions in serp_mentions.items():
                valid_positions = [p for p in positions if isinstance(p, int)]
                summary_results.append({
                    "Keyword": kw,
                    "SERP Feature": feature,
                    "Top Position": min(valid_positions) if valid_positions else "-",
                    "JSON URL": metadata.get("json_endpoint", "-"),
                    "HTML URL": metadata.get("raw_html_file", "-")
                })

            time.sleep(1.2)

    if summary_results:
        df = pd.DataFrame(summary_results)
        st.success("✅ Brand visibility summary:")

        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"visibility_{brand}_{datetime.today().strftime('%Y-%m-%d')}.csv",
            mime='text/csv',
            key="download-csv"
        )
    else:
        st.warning("⚠️ No brand mentions found in SERP features.")
