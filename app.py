import streamlit as st
import requests
import time
import re
import sqlite3
from io import BytesIO
from docx import Document
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from utils.resume_parser import parse_resume
from utils.matcher import (
    get_match_feedback,
    get_batched_match_feedback,
    get_custom_prompt_feedback,
    extract_score
)
from utils.prompt_templates import build_prompt
from utils.job_scraper.common import fetch_greenhouse_jobs, fetch_full_job_description
from utils.history import save_match, get_history

# -------------------- CONFIG --------------------
SUPPORTED_COMPANIES = {
    "Razorpay": "razorpaysoftwareprivatelimited",
    "Postman": "postman",
    "Turing": "turing",
    "Groww": "groww"
}

# -------------------- DB INIT --------------------
conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    source TEXT,  -- e.g., "google", "github", or "manual"
    password TEXT  -- will be NULL for OAuth users
)
''')
conn.commit()

# -------------------- SESSION SETUP --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# -------------------- DOCX HELPER --------------------
def generate_docx(text):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# -------------------- AUTH CONFIG --------------------
# Load config.yaml

with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Inject secrets
config["cookie"]["key"] = st.secrets["COOKIE_KEY"]
config["oauth"]["google"]["client_id"] = st.secrets["GOOGLE_CLIENT_ID"]
config["oauth"]["google"]["client_secret"] = st.secrets["GOOGLE_CLIENT_SECRET"]
config["oauth"]["github"]["client_id"] = st.secrets["GITHUB_CLIENT_ID"]
config["oauth"]["github"]["client_secret"] = st.secrets["GITHUB_CLIENT_SECRET"]

authenticator = stauth.Authenticate(
    credentials=config["credentials"],
    cookie_name=config["cookie"]["name"],
    key=config["cookie"]["key"],
    expiry_days=config["cookie"]["expiry_days"],
    oauth_credentials=config["oauth"]
)

login_info = authenticator.login(location="sidebar")

if login_info:
    name = login_info["name"]
    username = login_info["username"]
    auth_status = login_info["authenticated"]
else:
    name = username = None
    auth_status = None

# Handle login states
if auth_status:
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.name = name
    st.sidebar.success(f"👋 Welcome, {name}")

    # Insert OAuth user into DB if not exists
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if not c.fetchone():
        email = config["credentials"]["usernames"].get(username, {}).get("email", "unknown")
        c.execute('''
            INSERT INTO users (username, name, email, source, password)
            VALUES (?, ?, ?, ?, NULL)
        ''', (username, name, email, "oauth"))
        conn.commit()

    authenticator.logout("Logout", location="sidebar")

# -------------------- CACHE JOBS --------------------
if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

# -------------------- STYLING --------------------
st.set_page_config(page_title="LazyApply AI", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--background-color);
        color: var(--text-color);
    }
    h1, h2, h3 {
        font-weight: 600;
        color: var(--text-color);
    }
    .stButton button {
        background: linear-gradient(90deg, var(--primary-color), #5e5eea);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 12px;
        padding: 8px 16px;
        box-shadow: 0 0 8px rgba(75, 222, 145, 0.3);
        transition: all 0.3s ease-in-out;
    }
    .stButton button:hover {
        filter: brightness(1.05);
        box-shadow: 0 0 12px rgba(94, 94, 234, 0.5);
    }
    .stDownloadButton button {
        background: #222;
        color: white;
        border-radius: 12px;
        font-weight: bold;
    }
    .stDownloadButton button:hover {
        background: #000;
    }
    .stTextInput>div>div>input,
    .stTextArea textarea {
        background-color: var(--background-color);
        color: var(--text-color);
        border-radius: 10px;
        border: 1px solid #dce6f7;
        padding: 10px;
    }
    .stRadio>div>label {
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='
    text-align: center;
    font-family: "Poppins", sans-serif;
    font-weight: 600;
    font-size: 2.5rem;
    margin-top: 10px;
    color: var(--text-color);
'>
🤖 LazyApply AI
</h1>
<p style='
    text-align: center;
    font-size: 1rem;
    color: var(--text-color);
    opacity: 0.6;
    margin-top: -12px;
'>
Your Job Buddy for the Resume Revolution 🚀
</p>
""", unsafe_allow_html=True)

# -------------------- MAIN UI --------------------
tab1, tab2 = st.tabs(["📄 Match Resume", "𞳻 Explore Jobs"])

with tab1:
    st.markdown("Upload your resume and paste a job description to get tailored AI feedback.") 
    st.markdown("💡 Tip: Use your favorite job post!")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"], help="Only used locally. Never leaves your browser.")
    jd_text = st.text_area("💼 Paste the job description here", height=250, placeholder="Copy from LinkedIn, Naukri, or anywhere... 📝")

    mode = st.selectbox("🧠 Choose AI Analysis Mode", [
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

    section = st.selectbox("🔹 Focus on a specific resume section?", [
        "Entire Resume", "Professional Summary", "Experience", "Education", "Projects"
    ]) if mode == "Rewrite to Sound Results-Driven" else "Entire Resume"

    model_choice = st.radio("Choose model:", ["Exaone (Deep & Accurate)", "Mistral (Fast & Light)"], index=0, horizontal=True)
    chosen_model = "lgai/exaone-3-5-32b-instruct" if "Exaone" in model_choice else "mistralai/Mistral-7B-Instruct-v0.2"

    resume_text = parse_resume(uploaded_file) if uploaded_file else None
    submitted = st.button("🚀 Generate Feedback", help="Click once both resume and JD are ready")

    if submitted and resume_text and resume_text.strip() and jd_text.strip():
        key_hash = hash(resume_text + jd_text + mode + section + chosen_model)

        if st.session_state.get("input_hash") != key_hash:
            with st.spinner("🔬 Processing your resume..."):
                if mode == "Tailor Resume for Job Description" and not jd_text:
                    st.warning("This mode works best with a job description pasted above.")

                result, score = get_custom_prompt_feedback(
                    resume_text=resume_text,
                    jd_text=jd_text,
                    mode=mode,
                    section=section,
                    model=chosen_model
                )
                st.session_state["input_hash"] = key_hash
                st.session_state["feedback"] = str(result)
                st.session_state["copied"] = False

                save_match(resume_text, jd_text, result)
        else:
            result = st.session_state["feedback"]

        result = str(result) if result else "⚠️ No result generated."
        st.text_area("📊 AI Feedback", result, height=300)

    elif submitted:
        if not uploaded_file and not jd_text.strip():
            st.info("Upload your resume and paste a job description to begin.")
        elif not uploaded_file:
            st.warning("Please upload your resume.")
        elif not jd_text.strip():
            st.warning("Please paste a job description.")

with tab2:
    st.markdown("🧠 Select a company and search job roles:")
    selected_company = st.selectbox("🏢 Choose a company", list(SUPPORTED_COMPANIES.keys()))
    company_slug = SUPPORTED_COMPANIES[selected_company]
    keyword = st.text_input("🔍 Search by keyword", value="engineering")

    if keyword:
        jobs = fetch_greenhouse_jobs(company_slug, limit=10, keyword=keyword)
        if isinstance(jobs, str):
            st.error(jobs)
        elif not jobs:
            st.warning("No roles found for this keyword.")
        else:
            for job in jobs:
                with st.expander(f"🔧 {job['title']} – {job['location']}"):
                    st.markdown(f"**Company**: {selected_company}")
                    st.markdown(f"**Location**: {job['location']}")
                    st.markdown(f"**Link**: [Apply Here]({job['link']})")

                    if uploaded_file:
                        unique_key = f"{job['title']}_{job['link'].split('/')[-1]}"
                        if st.button(f"⚡ Match My Resume with {job['title']}", key=unique_key):
                            resume_text = parse_resume(uploaded_file)
                            with st.spinner("Matching in progress..."):
                                feedback = get_match_feedback(resume_text, job['summary'])
                            st.success("✅ Match completed!")
                            st.text_area("📊 Feedback", feedback if isinstance(feedback, str) else feedback[0], height=300)
                    else:
                        st.info("Upload resume in Tab 1 to enable matching.")
    else:
        st.info("Please enter a keyword to search job roles.")
