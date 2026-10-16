"""BestCV's focused Streamlit workspace."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
st.set_page_config(page_title="BestCV · Resume review", page_icon=":material/description:",
                   layout="wide", initial_sidebar_state="auto")

from frontend.services import supabase_client

AUTH_KEYS = ("access_token", "refresh_token", "user_id", "user_email")
for key in AUTH_KEYS:
    st.session_state.setdefault(key, None)
st.session_state.setdefault("current_view", "scorer")
if st.session_state.current_view not in ("scorer", "history"):
    st.session_state.current_view = "scorer"

css_path = Path(__file__).parent / "assets" / "styles.css"
st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def _set_session(result):
    for key in AUTH_KEYS:
        st.session_state[key] = result.get("email" if key == "user_email" else key)


def _sign_out():
    supabase_client.sign_out()
    for key in AUTH_KEYS:
        st.session_state[key] = None
    for key in ("scorer_analysis", "scorer_pdf_bytes", "scorer_filename", "scorer_show_results"):
        st.session_state.pop(key, None)
    st.session_state.current_view = "scorer"
    st.rerun()


@st.dialog("Welcome to BestCV")
def _account_dialog():
    st.caption("Sign in to analyze your resume and keep your reviews in one place.")
    if supabase_client._missing_config():
        st.info("Sign-in is not available yet. Complete the account setup to start analyzing resumes.")
        return
    sign_in, sign_up = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("signin_form"):
            email = st.text_input("Email", placeholder="you@example.com", key="signin_email")
            password = st.text_input("Password", type="password", key="signin_pw")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            if not email.strip() or not password:
                st.error("Enter your email and password.")
            else:
                result = supabase_client.sign_in_with_password(email.strip(), password)
                if "error" in result:
                    st.error(result["error"])
                else:
                    _set_session(result)
                    st.rerun()
    with sign_up:
        with st.form("signup_form"):
            email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            password = st.text_input("Password", type="password", help="Use at least 6 characters.", key="signup_pw")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            if not email.strip() or len(password) < 6:
                st.error("Enter your email and a password with at least 6 characters.")
            else:
                result = supabase_client.sign_up_with_password(email.strip(), password)
                if "error" in result:
                    st.error(result["error"])
                elif result.get("pending_confirmation"):
                    st.info("Check your inbox to confirm your email, then sign in.")
                else:
                    _set_session(result)
                    st.rerun()
    oauth = supabase_client.google_oauth_url()
    if oauth.get("url"):
        st.caption("Or continue with your Google account")
        st.link_button("Continue with Google", oauth["url"], use_container_width=True)


if not st.session_state.access_token and "code" in st.query_params:
    result = supabase_client.exchange_code_for_session(st.query_params["code"])
    st.query_params.clear()
    if "error" in result:
        st.session_state.auth_error = result["error"]
    else:
        _set_session(result)
        st.rerun()

with st.sidebar:
    st.markdown('<div class="bc-brand" aria-label="BestCV">Best<span>CV</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="bc-nav-label">WORKSPACE</div>', unsafe_allow_html=True)
    for label, view, icon in (("Analyze resume", "scorer", ":material/description:"),
                              ("History", "history", ":material/history:")):
        if st.button(label, icon=icon, key=f"nav_{view}", use_container_width=True,
                     type="primary" if st.session_state.current_view == view else "secondary"):
            st.session_state.current_view = view
            st.rerun()

breadcrumb, account = st.columns([6, 1.4], vertical_alignment="center")
with breadcrumb:
    current = "Resume review" if st.session_state.current_view == "scorer" else "History"
    st.markdown(f'<div class="bc-topline">Workspace <span>/</span> <strong>{current}</strong></div>', unsafe_allow_html=True)
with account:
    if st.session_state.access_token:
        with st.popover("Account", icon=":material/person:", use_container_width=True):
            st.caption(st.session_state.user_email or "Signed in")
            if st.button("Sign out", use_container_width=True):
                _sign_out()
    elif st.button("Sign in", icon=":material/login:", use_container_width=True, key="open_account"):
        _account_dialog()

if st.session_state.pop("auth_error", None):
    st.error("We could not complete sign-in. Please try again.")

if st.session_state.current_view == "history":
    from frontend.views import history
    history.render()
else:
    from frontend.views import scorer
    scorer.render()

if st.session_state.pop("show_auth_dialog", False):
    _account_dialog()
