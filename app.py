import streamlit as st
import sqlite3
import requests
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback

# -------------------- DB INIT --------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

# -------------------- OAUTH SETUP --------------------
GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
GITHUB_CLIENT_ID = st.secrets["GITHUB_CLIENT_ID"]
GITHUB_CLIENT_SECRET = st.secrets["GITHUB_CLIENT_SECRET"]

REDIRECT_URI = "https://lazyapply.streamlit.app"  # change if using custom domain

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------- SIDEBAR LOGIN --------------------
st.sidebar.markdown("## 🔐 Login")

query_params = st.experimental_get_query_params()

def handle_google_callback():
    code = query_params.get("code")
    if not code:
        return
    code = code[0]
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data=data).json()
    access_token = response.get("access_token")

    if access_token:
        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()
        login_user(userinfo["email"], userinfo["name"], "google")

def handle_github_callback():
    code = query_params.get("code")
    if not code:
        return
    code = code[0]
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code
    }
    response = requests.post(token_url, data=data, headers=headers).json()
    access_token = response.get("access_token")

    if access_token:
        userinfo = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        ).json()
        login_user(userinfo["login"], userinfo.get("name", userinfo["login"]), "github")

def login_user(username, name, source):
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.name = name
    st.session_state.source = source

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, name, email, source) VALUES (?, ?, ?, ?)",
                  (username, name, username, source))
        conn.commit()

    st.experimental_set_query_params()

# -------------------- HANDLE CALLBACK --------------------
if "code" in query_params:
    if "google" in query_params.get("state", [""])[0]:
        handle_google_callback()
    elif "github" in query_params.get("state", [""])[0]:
        handle_github_callback()

# -------------------- LOGIN/LOGOUT UI --------------------
if not st.session_state.logged_in:
    google_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&state=google"
    )
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=read:user"
        f"&state=github"
    )

    st.sidebar.markdown(f"[🔑 Sign in with Google]({google_url})", unsafe_allow_html=True)
    st.sidebar.markdown(f"[🐙 Sign in with GitHub]({github_url})", unsafe_allow_html=True)
    st.sidebar.info("Login to unlock personalized features.")
else:
    st.sidebar.success(f"👋 Welcome {st.session_state.name}")
    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

# -------------------- MAIN --------------------
st.title("LazyApply AI – MVP")
st.write("✅ OAuth login working, database stores users, ready to demo!")

# (Optional) Add job/resume tools below here.
