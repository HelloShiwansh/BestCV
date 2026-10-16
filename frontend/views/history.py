from datetime import datetime, timedelta, timezone
from html import escape
import math

import requests
import streamlit as st

from frontend.services import api_client


def _show_backend_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("Your saved analyses are unavailable right now. Check that the server is running and try again.")
    elif isinstance(exc, requests.Timeout):
        st.error("Loading your analyses took too long. Please try again.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        if exc.response.status_code in (401, 403):
            st.error("Please sign in again to view your analyses.")
        else:
            st.error("We couldn't load your saved analyses. Please try again.")
    else:
        st.error("We couldn't load your saved analyses. Please try again.")


def _score(value, maximum: int = 100) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if not math.isfinite(number):
        return "—"
    return f"{number:.0f}/{maximum}"


def _date_label(value) -> str:
    try:
        created_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return "Date unavailable"
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    local_date = created_at.astimezone(timezone(timedelta(hours=5, minutes=30)))
    return f"{local_date.day} {local_date:%b %Y} · {local_date:%I:%M %p} IST"


def _empty_state(title: str, description: str) -> None:
    st.markdown(
        '<div class="bc-empty-state">'
        f'<div class="bc-empty-heading" role="heading" aria-level="3">{escape(title)}</div>'
        f'<p>{escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def _show_analysis(analysis: dict, filename: str) -> None:
    st.session_state["scorer_analysis"] = analysis
    st.session_state["scorer_filename"] = filename
    st.session_state["scorer_show_results"] = True
    st.session_state.pop("scorer_pdf_bytes", None)
    st.session_state["current_view"] = "scorer"
    st.rerun()


def _render_entry(entry: dict, index: int, access_token: str) -> None:
    filename = str(entry.get("filename") or "Resume")
    analysis = entry.get("analysis_result") or {}
    component_scores = analysis.get("component_scores") or {}
    jd_comparison = analysis.get("jd_comparison") or analysis.get("jd_match_analysis") or {}
    entry_id = entry.get("id")
    entry_key = f"history_{entry_id or index}"

    with st.container(border=True):
        summary, score_column = st.columns([5, 1.5], vertical_alignment="center")
        with summary:
            st.markdown(
                f'<div class="bc-history-title">{escape(filename)}</div>'
                f'<div class="bc-history-meta">{escape(_date_label(entry.get("created_at")))}</div>',
                unsafe_allow_html=True,
            )
        with score_column:
            score = _score(entry.get("ats_score", analysis.get("ATS_score")))
            st.markdown(
                f'<div class="bc-history-score">{score}</div>'
                '<div class="bc-history-score-label">ATS score</div>',
                unsafe_allow_html=True,
            )
        if jd_comparison:
            match = _score(jd_comparison.get("match_percentage")).replace("/100", "%")
            st.caption(f"Job match · {match}")

        actions, _, delete = st.columns([2, 3, 1.5])
        with actions:
            if st.button("View analysis", key=f"{entry_key}_view", disabled=not analysis, use_container_width=True):
                _show_analysis(analysis, filename)
        with delete:
            if entry_id:
                with st.popover("Delete", use_container_width=True):
                    st.markdown("**Delete this analysis?**")
                    st.caption("This permanently removes the saved result from your history.")
                    if st.button("Delete permanently", key=f"{entry_key}_delete", use_container_width=True):
                        try:
                            api_client.delete_history_entry(str(entry_id), access_token)
                        except requests.RequestException as exc:
                            _show_backend_error(exc)
                        else:
                            st.toast("Analysis deleted.")
                            st.rerun()

        if component_scores:
            with st.expander("Score breakdown"):
                columns = st.columns(2)
                components = [
                    ("Formatting", "formatting", 20),
                    ("Keywords", "keywords", 25),
                    ("Content", "content", 25),
                    ("Skill validation", "skill_validation", 15),
                    ("ATS compatibility", "ats_compatibility", 15),
                ]
                for position, (label, key, maximum) in enumerate(components):
                    with columns[position % 2]:
                        st.markdown(f"{label} · **{_score(component_scores.get(key), maximum)}**")


def render() -> None:
    st.title("Analysis history")
    st.caption("Your saved resume analyses, ready when you need them.")

    access_token = st.session_state.get("access_token")
    if not access_token:
        _empty_state(
            "Sign in to view your analyses",
            "Use Sign in above to access your saved results.",
        )
        return

    try:
        history = api_client.get_history(access_token)
    except requests.RequestException as exc:
        _show_backend_error(exc)
        return

    if not history:
        _empty_state("No analyses yet", "Analyze your first resume to save a result here.")
        if st.button("Analyze a resume", type="primary"):
            st.session_state["current_view"] = "scorer"
            st.rerun()
        return

    count = len(history)
    st.caption(f"{count} saved {'analysis' if count == 1 else 'analyses'}")
    for index, entry in enumerate(history):
        _render_entry(entry, index, access_token)
