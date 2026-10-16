from typing import Any, Dict

import streamlit as st

from frontend.components.score_display import display_overall_score, display_score_breakdown
from frontend.components.strengths_issues import display_strengths, display_critical_issues
from frontend.components.skill_validation import display_skill_validation
from frontend.components.jd_comparison import display_jd_comparison
from frontend.components.detailed_feedback import display_detailed_feedback
from frontend.components.action_items import display_action_items
from frontend.components.recommendations import display_recommendations
from frontend.components._helpers import display_keywords, unique_strings


def display_results_dashboard(analysis: Dict[str, Any]) -> None:
    """
    Render the full results page from one backend response dict.

    `analysis` is the JSON body returned by POST /api/v1/analyze-resume
    (i.e. an AnalysisResponse). No transformation is done here — every
    section reads the fields it needs directly.
    """
    display_overall_score(analysis)
    overview, keywords, improvements = st.tabs(["Overview", "Keywords", "Improvements"])

    with overview:
        display_score_breakdown(analysis)
        display_strengths(analysis.get("strengths") or [])

    with keywords:
        # The two names are aliases in current responses; render just one.
        jd_comparison = analysis.get("jd_comparison") or analysis.get("jd_match_analysis")
        if jd_comparison:
            display_jd_comparison(jd_comparison)
        else:
            detected = unique_strings(analysis.get("matched_keywords") or analysis.get("skills") or [])
            if detected:
                st.markdown("### Detected keywords")
                display_keywords(detected)
            else:
                st.caption("No keywords were detected in this resume.")
        display_skill_validation(analysis)

    with improvements:
        detailed = analysis.get("detailed_feedback") or []
        if detailed:
            display_detailed_feedback(analysis)
            # Summary fields often repeat the detailed issue titles verbatim.
            covered = {str(issue.get("issue_title", "")).strip().casefold() for issue in detailed}
            additional = dict(analysis)
            for field in ("critical_issues", "issues_summary"):
                additional[field] = [item for item in analysis.get(field) or []
                                     if str(item).strip().casefold() not in covered]
            display_critical_issues(additional)
            display_recommendations(analysis)
        else:
            display_critical_issues(analysis)
            display_action_items(analysis)
            if not any(analysis.get(field) for field in ("critical_issues", "issues_summary", "suggestions")):
                st.caption("No improvements were flagged in this analysis.")
