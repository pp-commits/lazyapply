import streamlit as st
import sqlite3
from utils.resume_parser import parse_resume
from utils.matcher import get_custom_prompt_feedback, get_match_feedback
from utils.job_scraper.common import fetch_greenhouse_jobs
from utils.history import save_match
from io import BytesIO
from docx import Document
import requests
import base64

# -------------------- CONFIG --------------------
SUPPORTED_COMPANIES = {
    "Razorpay": "razorpaysoftwareprivatelimited",
    "Postman": "postman",
    "Turing": "turing",
    "Groww": "groww"
}

# -------------------- DB INIT --------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    source TEXT
)
''')
conn.commit()

# -------------------- SESSION INIT --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "name" not in st.session_state:
    st.session_state.name = None

# -------------------- DOCX HELPER --------------------
def generate_docx(text):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# -------------------- OAUTH CALLBACK HANDLER --------------------
def handle_oauth_callback():
    params = st.query_params
    provider = params.get("provider", [None])[0]
    code = params.get("code", [None])[0]

    if provider and code:
        if provider == "google":
            client_id = st.secrets["GOOGLE_CLIENT_ID"]
            client_secret = st.secrets["GOOGLE_CLIENT_SECRET"]
            token_url = "https://oauth2.googleapis.com/token"
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        elif provider == "github":
            client_id = st.secrets["GITHUB_CLIENT_ID"]
            client_secret = st.secrets["GITHUB_CLIENT_SECRET"]
            token_url = "https://github.com/login/oauth/access_token"
            userinfo_url = "https://api.github.com/user"
        else:
            st.error("Unknown OAuth provider.")
            return

        redirect_uri = "https://lazyapply.streamlit.app"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        headers = {"Accept": "application/json"}
        response = requests.post(token_url, data=data, headers=headers)
        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            st.error("OAuth failed. Could not retrieve access token.")
            return

        userinfo = requests.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"}).json()

        if provider == "google":
            username = userinfo.get("email")
            name = userinfo.get("name")
        else:
            username = str(userinfo.get("id"))
            name = userinfo.get("login")

        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.name = name

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not c.fetchone():
            c.execute("INSERT INTO users (username, name, email, source) VALUES (?, ?, ?, ?)",
                      (username, name, username, provider))
            conn.commit()

        st.success(f"✅ Logged in as {name}")
        st.rerun()

# -------------------- AUTH UI --------------------
def login_ui():
    st.sidebar.markdown("### 🔐 Login or Sign Up")

    google_link = (
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={st.secrets['GOOGLE_CLIENT_ID']}"
        f"&response_type=code&scope=openid%20email%20profile"
        f"&redirect_uri={st.request.url}&state=login&access_type=offline&prompt=consent"
        f"&provider=google"
    )
    github_link = (
        f"https://github.com/login/oauth/authorize?client_id={st.secrets['GITHUB_CLIENT_ID']}"
        f"&redirect_uri={st.request.url}&scope=read:user%20user:email&state=login&provider=github"
    )

    st.sidebar.markdown(f"[🔵 Sign in with Google]({google_link})")
    st.sidebar.markdown(f"[⚫ Sign in with GitHub]({github_link})")

# -------------------- AUTH CHECK --------------------
handle_oauth_callback()

if not st.session_state.logged_in:
    login_ui()
else:
    st.sidebar.markdown(f"👋 Welcome, **{st.session_state.name}**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="LazyApply AI", layout="centered")

# -------------------- CACHE JOBS --------------------
if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

# -------------------- UI --------------------
st.title("🤖 LazyApply AI")
st.caption("Your Job Buddy for the Resume Revolution 🚀")

tab1, tab2 = st.tabs(["📄 Match Resume", "𞳻 Explore Jobs"])

with tab1:
    uploaded_file = st.file_uploader("📄 Upload your resume", type=["pdf", "docx"])
    jd_text = st.text_area("💼 Paste job description")

    mode = st.selectbox("AI Mode", [
        "Brutal Resume Review",
        "Rewrite to Sound Results-Driven",
        "Optimize for ATS",
        "Generate Professional Summary",
        "Tailor Resume for Job Description",
        "Top 1% Candidate Benchmarking",
        "Generate Cover Letter",
        "Suggest Resume Format",
        "Full Resume Intelligence Report"
    ])

    section = st.selectbox("Focus section", [
        "Entire Resume", "Professional Summary", "Experience", "Education", "Projects"
    ]) if mode == "Rewrite to Sound Results-Driven" else "Entire Resume"

    model = st.radio("Model", ["Exaone", "Mistral"], horizontal=True)
    chosen_model = "lgai/exaone-3-5-32b-instruct" if model == "Exaone" else "mistralai/Mistral-7B-Instruct-v0.2"

    resume_text = parse_resume(uploaded_file) if uploaded_file else None
    if st.button("🚀 Generate Feedback") and resume_text and jd_text:
        result, score = get_custom_prompt_feedback(
            resume_text=resume_text,
            jd_text=jd_text,
            mode=mode,
            section=section,
            model=chosen_model
        )
        save_match(resume_text, jd_text, result)
        st.text_area("📊 AI Feedback", result, height=300)

with tab2:
    company = st.selectbox("🏢 Company", list(SUPPORTED_COMPANIES.keys()))
    keyword = st.text_input("🔍 Role Keyword", value="engineering")
    if keyword:
        jobs = fetch_greenhouse_jobs(SUPPORTED_COMPANIES[company], limit=10, keyword=keyword)
        for job in jobs:
            with st.expander(f"🔧 {job['title']} – {job['location']}"):
                st.markdown(f"**Link**: [Apply Here]({job['link']})")
                if uploaded_file:
                    if st.button(f"⚡ Match with {job['title']}", key=job['link']):
                        feedback = get_match_feedback(parse_resume(uploaded_file), job['summary'])
                        st.text_area("📊 Feedback", feedback, height=300)
