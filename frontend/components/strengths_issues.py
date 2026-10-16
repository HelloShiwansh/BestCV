from typing import Any, Dict, List
import streamlit as st

from frontend.components._helpers import unique_strings


def display_strengths(strengths: List[str]) -> None:
    strengths = unique_strings(strengths)
    if not strengths:
        return
    st.markdown("### What works well")
    for item in strengths:
        st.markdown(f"- {item}")


def display_critical_issues(analysis: Dict[str, Any]) -> None:
    critical = unique_strings(analysis.get("critical_issues") or [])
    summary = unique_strings(analysis.get("issues_summary") or [])

    if not critical and not summary:
        return

    st.markdown("### Areas to improve")

    for item in critical:
        st.markdown(f"- {item}")

    critical_labels = {item.casefold() for item in critical}
    extra = [s for s in summary if s.casefold() not in critical_labels]
    if extra:
        with st.expander("Additional feedback" if critical else "Feedback", expanded=not critical):
            for item in extra:
                st.markdown(f"- {item}")
