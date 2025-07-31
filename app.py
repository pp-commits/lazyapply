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

        redirect_uri = "https://lazyapply.streamlit.app/oauth2callback"
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
        f"&redirect_uri=https://lazyapply.streamlit.app/oauth2callback"
        f"&state=login&access_type=offline&prompt=consent"
    )

    st.sidebar.markdown(f"[🔐 Login with Google]({google_link})", unsafe_allow_html=True)

# -------------------- AUTH CHECK --------------------
handle_oauth_callback()

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="LazyApply AI", layout="centered")

# -------------------- UI HEADER --------------------
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

# -------------------- LOGOUT HANDLER --------------------
if st.session_state.logged_in and st.query_params.get("logout"):
    st.session_state.clear()
    st.rerun()

# -------------------- AUTH BLOCK --------------------
if not st.session_state.logged_in:
    login_ui()
    st.stop()

# -------------------- CACHE JOBS --------------------
if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

# -------------------- MAIN UI --------------------
st.caption("Your Job Buddy for the Resume Revolution 🚀")
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
