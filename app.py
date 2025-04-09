def scan_json(obj, parent_key="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, (dict, list)):
                scan_json(v, new_key)
            elif isinstance(v, str) and brand.lower() in v.lower():
                base_feature = get_serp_feature_label(parent_key)
                sub_feature = obj.get("category") or obj.get("block_title")
                feature_label = f"{base_feature}::{sub_feature}" if sub_feature else base_feature
                fields = context_fields_by_feature.get(base_feature, context_fields_by_feature["default"])

                # Try to extract meaningful context
                context_candidates = [obj.get(field) for field in fields if obj.get(field)]
                if context_candidates:
                    context = next((c for c in context_candidates if c and c.lower() != brand.lower()), "-")
                else:
                    # Fallback: aggregate all string fields if no known context
                    context = " | ".join([str(val) for val in obj.values() if isinstance(val, str) and brand.lower() in val.lower()])
                    if not context:
                        context = "-"

                position = obj.get("position", "-")
                match_id = (keyword, feature_label, context)
                if match_id not in seen_matches:
                    seen_matches.add(match_id)
                    results_list.append({
                        "Keyword": keyword,
                        "SERP Feature": feature_label,
                        "Context": context,
                        "Position": position,
                        "JSON URL": metadata.get("json_endpoint", "-"),
                        "HTML URL": metadata.get("raw_html_file", "-")
                    })
    elif isinstance(obj, list):
        for item in obj:
            scan_json(item, parent_key)
