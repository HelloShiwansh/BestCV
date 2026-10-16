from html import escape
from typing import Iterable, List, Tuple

import streamlit as st


def get_score_color(score: float) -> Tuple[str, str]:
    """Return (text_color, background_color) for a 0–100 score."""
    if score >= 80:
        return "#7856b5", "#f1eafa"
    if score >= 60:
        return "#9b704f", "#fff1e7"
    return "#ad5972", "#fceef2"


def get_score_emoji(score: float) -> str:
    """Emoji that matches the score band — used in headlines."""
    if score >= 90:
        return "🌟"
    if score >= 80:
        return "✅"
    if score >= 70:
        return "👍"
    if score >= 60:
        return "⚠️"
    return "🔴"


def get_severity_style(severity: str) -> Tuple[str, str, str]:
    """
    Return (icon, text_color, background_color) for an IssueDetail severity.
    Matches the values the backend emits in `detailed_feedback[].severity_level`.
    """
    level = (severity or "").lower()
    if level in ("critical", "high"):
        return "🔴", "#c62828", "#ffebee"
    if level == "medium":
        return "🟡", "#f57c00", "#fff3e0"
    return "🟢", "#2e7d32", "#e8f5e9"


def unique_strings(values: Iterable[str]) -> List[str]:
    """Keep the first occurrence of each nonempty label, in display order."""
    result: List[str] = []
    seen = set()
    for value in values:
        label = str(value).strip()
        normalized = " ".join(label.casefold().split())
        if normalized and normalized not in seen:
            result.append(label)
            seen.add(normalized)
    return result


def display_keywords(values: Iterable[str], *, missing: bool = False) -> None:
    """Render plain text labels as compact chips; resume content stays escaped."""
    labels = unique_strings(values)
    if not labels:
        return
    class_name = "bc-keyword bc-keyword-missing" if missing else "bc-keyword"
    chips = "".join(
        f'<span class="{class_name}">{escape(label)}</span>' for label in labels
    )
    st.markdown(f'<div class="bc-keyword-list">{chips}</div>', unsafe_allow_html=True)
