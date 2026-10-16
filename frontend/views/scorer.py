"""Upload, review, and export without extra modes or navigation."""
import requests
import streamlit as st

from frontend.components.dashboard import display_results_dashboard
from frontend.components._helpers import unique_strings
from frontend.services import api_client

MAX_RESUME_BYTES = 5 * 1024 * 1024


def _read_jd(jd_file, jd_text: str) -> str:
    if jd_text.strip():
        return jd_text.strip()
    if jd_file is not None:
        return jd_file.getvalue().decode("utf-8", errors="ignore").strip()
    return ""


def _show_backend_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("The analysis service is unavailable. Please try again shortly.")
    elif isinstance(exc, requests.Timeout):
        st.error("This review is taking longer than expected. Please try again.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", "We could not analyze this resume.")
        except ValueError:
            detail = "We could not analyze this resume. Please try again."
        st.error(detail)
    else:
        st.error("Something went wrong. Please try again.")


def _summary_text(analysis: dict) -> str:
    score = analysis.get("ATS_score", analysis.get("ats_score", 0))
    lines = [f"BestCV Resume Review\nATS score: {score:.0f}/100", ""]
    if analysis.get("interpretation"):
        lines.extend([analysis["interpretation"], ""])
    seen = set()

    def add_section(title, items):
        remaining = []
        for item in unique_strings(items):
            normalized = " ".join(item.casefold().split())
            if normalized not in seen:
                remaining.append(item)
                seen.add(normalized)
        if remaining:
            lines.extend([title, *(f"- {item}" for item in remaining), ""])

    add_section("What works well", analysis.get("strengths") or [])
    for issue in analysis.get("detailed_feedback") or []:
        title = issue.get("issue_title") or "Improvement"
        seen.add(" ".join(title.casefold().split()))
        add_section(title, [issue.get("how_to_fix") or "", *(issue.get("action_items") or [])])
    add_section("Areas to improve", [*(analysis.get("critical_issues") or []),
                                      *(analysis.get("issues_summary") or [])])
    add_section("Next steps", analysis.get("suggestions") or [])
    return "\n".join(lines)


def _render_export_buttons(analysis: dict) -> None:
    with st.expander("Download your review", icon=":material/download:"):
        pdf_col, text_col = st.columns(2)
        with pdf_col:
            if "scorer_pdf_bytes" not in st.session_state:
                if st.button("Prepare PDF", icon=":material/picture_as_pdf:", use_container_width=True):
                    try:
                        with st.spinner("Preparing your report…"):
                            st.session_state.scorer_pdf_bytes = api_client.generate_pdf(
                                analysis, access_token=st.session_state["access_token"])
                    except requests.RequestException as exc:
                        _show_backend_error(exc)
            if st.session_state.get("scorer_pdf_bytes"):
                st.download_button("Download PDF", st.session_state.scorer_pdf_bytes,
                                   "bestcv-review.pdf", "application/pdf",
                                   use_container_width=True, key="download_pdf_report")
        with text_col:
            st.download_button("Download text summary", _summary_text(analysis),
                               "bestcv-summary.txt", "text/plain",
                               use_container_width=True, key="download_summary")


def _new_review():
    for key in ("scorer_analysis", "scorer_pdf_bytes", "scorer_filename", "scorer_show_results",
                "resume_upload", "jd_text", "jd_upload"):
        st.session_state.pop(key, None)
    st.rerun()


def render() -> None:
    analysis = st.session_state.get("scorer_analysis")
    if analysis and st.session_state.get("scorer_show_results"):
        heading, action = st.columns([4, 1], vertical_alignment="bottom")
        with heading:
            st.title("Your resume review")
            st.caption(st.session_state.get("scorer_filename") or "Resume analysis")
        with action:
            if st.button("New review", icon=":material/add:", use_container_width=True):
                _new_review()
        display_results_dashboard(analysis)
        _render_export_buttons(analysis)
        return

    st.markdown('<div class="bc-page-intro"><h1>Improve your <span class="bc-title-accent">resume.</span></h1>'
                '<p>See what’s working, what’s missing, and where to focus next.</p></div>', unsafe_allow_html=True)

    resume_col, jd_col = st.columns(2, gap="medium")
    with resume_col, st.container(border=True, key="resume_card"):
        st.markdown('<div class="bc-step-label"><b>01</b><span>YOUR RESUME</span></div>', unsafe_allow_html=True)
        st.subheader("Start with your resume")
        st.caption("A fresh look at your experience, skills, and structure.")
        resume_file = st.file_uploader("Upload your resume", type=["pdf", "docx"],
                                       label_visibility="collapsed", key="resume_upload")
        with st.container(key="resume_footer"):
            st.caption("PDF or DOCX · maximum 5 MB")
    with jd_col, st.container(border=True, key="jd_card"):
        st.markdown('<div class="bc-step-label"><b>02</b><span>TARGET ROLE</span><em>Optional</em></div>', unsafe_allow_html=True)
        st.subheader("Add a job description")
        st.caption("Get a closer match to the role you have in mind.")
        jd_text = st.text_area("Job description", placeholder="Paste the job description here…",
                               height=160, label_visibility="collapsed", key="jd_text")
        with st.container(key="jd_footer"):
            with st.popover("Upload a .txt file", icon=":material/attach_file:"):
                jd_file = st.file_uploader("Job description file", type=["txt"], key="jd_upload")
            if jd_file is not None:
                st.caption(f"Attached: {jd_file.name}" + (" · pasted text takes priority" if jd_text.strip() else ""))

    oversized = resume_file is not None and resume_file.size > MAX_RESUME_BYTES
    if oversized:
        st.error("Your resume is larger than 5 MB. Please upload a smaller file.")
    st.markdown('<div class="bc-action-spacer"></div>', unsafe_allow_html=True)
    action, note = st.columns([1.3, 3], vertical_alignment="center")
    with action:
        analyze = st.button("Analyze resume", icon=":material/arrow_forward:", type="primary",
                            use_container_width=True, disabled=resume_file is None or oversized)
    with note:
        st.caption("Sign in to analyze and save your review." if not st.session_state.get("access_token")
                   else "Leave the job description blank for a general review.")
    st.markdown('<div class="bc-bottom-note"><span>GOOD TO KNOW</span>'
                ' Use a resume with selectable text. Add a job description for a more focused review.</div>', unsafe_allow_html=True)
    if not analyze:
        return
    if not st.session_state.get("access_token"):
        st.session_state.show_auth_dialog = True
        st.rerun()
    job_description = _read_jd(jd_file, jd_text)
    try:
        with st.spinner("Reviewing your resume. This may take a moment…"):
            analysis = api_client.analyze_resume(resume_file, access_token=st.session_state.access_token,
                                                job_description=job_description)
    except requests.RequestException as exc:
        _show_backend_error(exc)
        return
    st.session_state.pop("scorer_pdf_bytes", None)
    st.session_state.scorer_analysis = analysis
    st.session_state.scorer_filename = resume_file.name
    st.session_state.scorer_show_results = True
    st.rerun()
