import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
from datetime import datetime
import time

# === Sidebar UI ===
st.sidebar.title("🔍 Woolroom Visibility Tracker")
api_key = st.sidebar.text_input("SerpAPI Key", type="password")
brand = st.sidebar.text_input("Brand Name to Track", "woolroom")
keywords_input = st.sidebar.text_area("Keywords (one per line)", "wool bedding\nwool pillow")

# Sample request to detect available features
def get_available_features(api_key):
    try:
        params = {
            "q": "wool bedding",
            "hl": "en",
            "gl": "us",
            "api_key": api_key
        }
        results = GoogleSearch(params).get_dict()
        return list(results.keys())
    except Exception as e:
        st.error(f"Error fetching features: {e}")
        return []

# Fetch feature options if API key is valid
available_features = get_available_features(api_key) if api_key else []
selected_features = st.sidebar.multiselect(
    "Select SERP features to track:",
    options=available_features,
    default=[f for f in available_features if f in ["organic_results", "related_questions", "knowledge_graph"]]
)

run = st.sidebar.button("Run Visibility Check")

# === Run the check ===
if run and api_key and keywords_input:
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
                value = results.get(feature, "-")
                if isinstance(value, list):
                    row[feature] = "Yes" if brand.lower() in str(value).lower() else "No"
                elif isinstance(value, dict):
                    if feature == "knowledge_graph":
                        website = value.get("website")
                        if website is None:
                            row[feature] = "-"
                        else:
                            row[feature] = "Yes" if brand.lower() in website.lower() else "No"
                    else:
                        row[feature] = "Yes" if brand.lower() in str(value).lower() else "No"
                else:
                    row[feature] = "-"

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
