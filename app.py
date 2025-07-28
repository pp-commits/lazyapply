import streamlit as st
import requests
import time
import re
import sqlite3
from io import BytesIO
from docx import Document
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

SUPPORTED_COMPANIES = {
    "Razorpay": "razorpaysoftwareprivatelimited",
    "Postman": "postman",
    "Turing": "turing",
    "Groww": "groww"
}

def generate_docx(text):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Initialize SQLite DB
conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)''')
conn.commit()

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Auth block
with st.sidebar:
    st.subheader("🔐 Login / Sign Up")
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (login_user, login_pass))
            if c.fetchone():
                st.success("Logged in successfully!")
                st.session_state.logged_in = True
                st.session_state.username = login_user
            else:
                st.error("Invalid credentials")

    with tab_signup:
        signup_user = st.text_input("New Username", key="signup_user")
        signup_pass = st.text_input("New Password", type="password", key="signup_pass")
        if st.button("Sign Up"):
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (signup_user, signup_pass))
                conn.commit()
                st.success("Account created! You can now login.")
            except sqlite3.IntegrityError:
                st.error("Username already exists.")

if not st.session_state.logged_in:
    st.info("Some features will unlock after login.")

if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

st.set_page_config(page_title="LazyApply AI", layout="centered")

# Style and Main UI Heading
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
