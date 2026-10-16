from typing import Any, Dict, Optional

import streamlit as st

from frontend.components._helpers import display_keywords, unique_strings


def display_jd_comparison(jd_comparison: Optional[Dict[str, Any]]) -> None:
    if not jd_comparison:
        return  # caller decides whether to render the section at all

    st.markdown("### Job match")

    match_pct = float(jd_comparison.get("match_percentage", 0))
    semantic = float(jd_comparison.get("semantic_similarity", 0))
    matched = unique_strings(jd_comparison.get("matched_keywords", []) or [])
    missing = unique_strings(jd_comparison.get("missing_keywords", []) or [])
    gap = unique_strings(jd_comparison.get("skills_gap", []) or [])

    top_l, top_r = st.columns(2)
    with top_l:
        st.metric("Overall match", f"{match_pct:.0f}%")
        st.progress(min(max(match_pct / 100.0, 0.0), 1.0))
    with top_r:
        st.metric("Context match", f"{semantic * 100:.0f}%")
        st.progress(min(max(semantic, 0.0), 1.0))

    if matched:
        st.markdown("**Matched keywords**")
        display_keywords(matched)
    if missing:
        st.markdown("**Missing keywords**")
        st.caption("Include relevant terms where they accurately reflect your experience.")
        display_keywords(missing, missing=True)
    missing_labels = {keyword.casefold() for keyword in missing}
    additional_gap = [skill for skill in gap if skill.casefold() not in missing_labels]
    if additional_gap:
        st.markdown("**Other skills to review**")
        display_keywords(additional_gap, missing=True)
