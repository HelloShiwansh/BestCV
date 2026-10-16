from typing import Any, Dict

import streamlit as st

from frontend.components._helpers import unique_strings


def display_recommendations(analysis: Dict[str, Any]) -> None:
    covered = []
    for issue in analysis.get("detailed_feedback") or []:
        covered.extend(issue.get("action_items") or [])
        covered.append(issue.get("how_to_fix") or "")
    covered_labels = {" ".join(str(item).casefold().split()) for item in covered}
    suggestions = [item for item in unique_strings(analysis.get("suggestions") or [])
                   if " ".join(item.casefold().split()) not in covered_labels]
    if not suggestions:
        return

    st.markdown("### More recommendations")
    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")
