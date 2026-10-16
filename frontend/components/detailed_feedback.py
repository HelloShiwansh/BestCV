from typing import Any, Dict, List

import streamlit as st

from frontend.components._helpers import unique_strings


SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def _group_by_severity(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {level: [] for level in SEVERITY_ORDER}
    for issue in issues:
        level = (issue.get("severity_level") or "low").lower()
        grouped.setdefault(level, []).append(issue)
    return grouped


def _render_issue(issue: Dict[str, Any]) -> None:
    title = issue.get("issue_title", "Untitled issue")
    severity = (issue.get("severity_level") or "low").lower()
    impact = issue.get("ats_impact", "")
    explanation = issue.get("explanation", "")
    where = issue.get("where_it_appears", "")
    how_to_fix = issue.get("how_to_fix", "")
    action_items = unique_strings(issue.get("action_items") or [])
    example = issue.get("example_improvement", "")

    priority = {"critical": "High priority", "high": "High priority", "medium": "Medium priority", "low": "Refinement"}.get(severity, "Refinement")
    with st.expander(f"{title} · {priority}", expanded=False):
        if impact:
            st.caption(impact)
        if explanation:
            st.write(explanation)
        if where:
            st.markdown(f"**Where it appears:** {where}")
        if how_to_fix:
            st.markdown(f"**How to fix:** {how_to_fix}")
        additional_actions = [item for item in action_items if item.casefold() != str(how_to_fix).strip().casefold()]
        if additional_actions:
            for item in additional_actions:
                st.markdown(f"- {item}")
        if example:
            st.markdown("**Example improvement:**")
            st.code(example, language="text")


def display_detailed_feedback(analysis: Dict[str, Any]) -> None:
    issues = analysis.get("detailed_feedback") or []
    if not issues:
        return  # backend produced no per-issue feedback this run

    st.markdown("### Improve your resume")
    st.caption("Start with the highest priority feedback. Open an item for specific guidance.")

    grouped = _group_by_severity(issues)
    for level in [*SEVERITY_ORDER, *(key for key in grouped if key not in SEVERITY_ORDER)]:
        items = grouped.get(level, [])
        if not items:
            continue
        for issue in items:
            _render_issue(issue)
