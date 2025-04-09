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

# Button to fetch features and store in session
if "available_features" not in st.session_state:
    st.session_state.available_features = []

if st.sidebar.button("Fetch SERP Features"):
    def get_available_features(api_key, query):
        try:
            if api_key:
                params = {
                    "q": query,
                    "hl": "en",
                    "gl": "us",
                    "api_key": api_key
                }
                results = GoogleSearch(params).get_dict()
                features = set(results.keys())

                # Include nested values as selectable labels for more clarity
                if "immersive_products" in results:
                    for item in results["immersive_products"]:
                        if isinstance(item, dict) and "category" in item:
                            features.add(f"immersive_products::{item['category']}")

                if "related_brands" in results:
                    for item in results["related_brands"]:
                        if isinstance(item, dict) and "block_title" in item:
                            features.add(f"related_brands::{item['block_title']}")

                return sorted(features)
        except Exception as e:
            st.error(f"Error fetching features: {e}")
        return []

    # Use first real keyword for feature fetching
    keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
    sample_keyword = keywords[0] if keywords else "test"
    st.session_state.available_features = get_available_features(api_key, sample_keyword)

selected_features = st.sidebar.multiselect(
    "Select SERP features to track:",
    options=st.session_state.available_features,
    default=[f for f in st.session_state.available_features if f in ["organic_results", "related_questions", "knowledge_graph"]]
)

run = st.sidebar.button("Run Visibility Check")

# === Run the check ===
if run and api_key and keywords_input and brand and selected_features:
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

            row = {"Keyword": keyword}
            for feature in selected_features:
                found = False

                # Split for nested category/feature
                if "::" in feature:
                    parent, child = feature.split("::", 1)
                    if parent == "immersive_products" and parent in results:
                        for item in results[parent]:
                            if item.get("category") == child and brand.lower() in str(item).lower():
                                found = True
                                break
                    elif parent == "related_brands" and parent in results:
                        for item in results[parent]:
                            if item.get("block_title") == child and brand.lower() in str(item.get("link", "")).lower():
                                found = True
                                break
                else:
                    # Direct top-level key
                    if feature in results:
                        value = results[feature]
                        if isinstance(value, list):
                            found = brand.lower() in str(value).lower()
                        elif isinstance(value, dict):
                            if feature == "knowledge_graph":
                                website = value.get("website")
                                if website:
                                    found = brand.lower() in website.lower()
                            else:
                                found = brand.lower() in str(value).lower()

                row[feature] = "Yes" if found else ("-" if feature not in results else "No")

            # Add metadata URLs
            metadata = results.get("search_metadata", {})
            row["JSON URL"] = metadata.get("json_endpoint", "-")
            row["HTML URL"] = metadata.get("raw_html_file", "-")

            results_list.append(row)
            time.sleep(1.2)

    df = pd.DataFrame(results_list)
    st.success("✅ Done! Here's your visibility report:")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"visibility_{brand}_{datetime.today().strftime('%Y-%m-%d')}.csv",
        mime='text/csv'
    )
