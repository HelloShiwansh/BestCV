from typing import Any, Dict, List, Tuple

import streamlit as st


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _collect_action_items(analysis: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Return list of (severity, source_title, action_text)."""
    items: List[Tuple[str, str, str]] = []

    for issue in analysis.get("detailed_feedback") or []:
        level = (issue.get("severity_level") or "low").lower()
        title = issue.get("issue_title", "")
        for action in issue.get("action_items") or []:
            items.append((level, title, action))

    if not items:
        for suggestion in analysis.get("suggestions") or []:
            items.append(("medium", "General", suggestion))

    items.sort(key=lambda row: SEVERITY_RANK.get(row[0], 99))
    unique_items = []
    seen = set()
    for row in items:
        normalized = " ".join(str(row[2]).casefold().split())
        if normalized and normalized not in seen:
            unique_items.append(row)
            seen.add(normalized)
    return unique_items


def display_action_items(analysis: Dict[str, Any]) -> None:
    items = _collect_action_items(analysis)
    if not items:
        return

    st.markdown("### Next steps")

    for level, source, action in items:
        st.markdown(f"- **{source}:** {action}" if source and source != "General" else f"- {action}")
