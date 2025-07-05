import streamlit as st
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback

st.set_page_config(page_title="LazyApplyAI – Match & Improve", layout="centered")

st.title("🧠 LazyApplyAI")
st.subheader("Phase 1: Resume + JD Matcher")

uploaded_file = st.file_uploader("Upload your Resume (.pdf or .docx)", type=["pdf", "docx"])
jd_text = st.text_area("Paste the Job Description", height=300)

if uploaded_file and jd_text:
    with st.spinner("Analyzing..."):
        resume_text = parse_resume(uploaded_file)
        feedback = get_match_feedback(resume_text, jd_text)
    st.markdown("### 🔍 Match Report")
    st.code(feedback)