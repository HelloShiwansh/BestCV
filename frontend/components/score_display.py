from html import escape
from typing import Any, Dict

import streamlit as st

from frontend.components._helpers import get_score_color


# Component max scores match backend/core/config.py SCORE_WEIGHTS.
# (Backend returns each component's score on its own scale, not 0–100.)
COMPONENTS = [
    ("Formatting",        "formatting",        20, ""),
    ("Keywords & skills", "keywords",          25, ""),
    ("Content quality",   "content",           25, ""),
    ("Skill evidence",    "skill_validation",  15, ""),
    ("ATS compatibility", "ats_compatibility", 15, ""),
]


def display_overall_score(analysis: Dict[str, Any]) -> None:
    """Compact summary, with the backend's interpretation and score unchanged."""
    score = float(analysis.get("ATS_score", analysis.get("ats_score", 0)))
    interpretation = escape(str(analysis.get("interpretation") or ""))
    text_color, _ = get_score_color(score)

    st.markdown(
        f"""
        <div class="bc-score-card">
            <div class="bc-score-number" style="color:{text_color}">
                {score:.0f}<span class="bc-score-label">/ 100</span>
            </div>
            <div class="bc-score-copy">
                <div class="bc-eyebrow">ATS resume score</div>
                <p>{interpretation}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_score_breakdown(analysis: Dict[str, Any]) -> None:
    """Five progress bars, one per scoring component."""
    component_scores = analysis.get("component_scores") or {}
    if not component_scores:
        return
    st.markdown("### Score breakdown")
    st.caption("Each category contributes to your score out of 100.")

    rows = []
    for label, key, max_score, _ in COMPONENTS:
        value = float(component_scores.get(key, 0))
        percentage = min(max(value / max_score, 0.0), 1.0)
        rows.append(
            f'<div class="bc-score-row">'
            f'<div class="bc-score-row-label"><span>{escape(label)}</span>'
            f'<span>{value:g}<span class="bc-score-max"> / {max_score}</span></span></div>'
            f'<div class="bc-score-track" role="progressbar" aria-label="{escape(label)}" '
            f'aria-valuenow="{value:g}" aria-valuemin="0" aria-valuemax="{max_score}">'
            f'<div class="bc-score-fill" style="width:{percentage * 100:g}%"></div>'
            '</div></div>'
        )
    st.markdown(''.join(rows), unsafe_allow_html=True)
