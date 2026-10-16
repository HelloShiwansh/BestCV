from typing import Any, Dict

import streamlit as st

from frontend.components._helpers import display_keywords, unique_strings


def display_skill_validation(analysis: Dict[str, Any]) -> None:
    details = analysis.get("skill_validation_details") or {}
    validated = details.get("validated", []) or []
    unvalidated = unique_strings(details.get("unvalidated", []) or [])
    total = details.get("total", len(validated) + len(unvalidated))
    pct = details.get("validation_pct", 0.0)

    if total == 0 and not validated and not unvalidated:
        return

    st.markdown("### Skill evidence")
    st.caption(f"{len(validated)} of {total} skills are supported by your experience or projects ({pct:.0f}%).")

    if validated:
        with st.expander(f"Supported skills · {len(validated)}", expanded=False):
            for entry in validated:
                skill = entry.get("skill", "?")
                projects = entry.get("projects", []) or []
                similarity = entry.get("similarity")

                project_text = ", ".join(projects[:3]) if projects else "experience section"
                sim_text = f" ({similarity * 100:.0f}% match)" if isinstance(similarity, (int, float)) else ""
                st.markdown(f"- **{skill}**{sim_text} — {project_text}")

    if unvalidated:
        st.markdown("**Add supporting evidence**")
        st.caption("Connect these skills to a project or an experience bullet.")
        display_keywords(unvalidated, missing=True)
