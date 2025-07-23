import streamlit as st
import requests
import time
import re
import plotly.graph_objects as go
import pandas as pd
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

if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

st.set_page_config(page_title="LazyApply AI", layout="centered")
st.markdown("""
    <h1 style='text-align: center; color: #4B4B4B; font-family: "Poppins", sans-serif;'>
    🤖 LazyApply AI <span style='font-size:0.8em; color: #888;'>Your Job Buddy</span>
    </h1>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📄 Match Resume", "𞳻 Explore Jobs"])

# ------------ Phase 1: Resume Matching ------------
with tab1:
    st.markdown("Upload your resume and paste a job description to get tailored AI feedback. 💡 Tip: Use your favorite job post!")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"], help="Only used locally. Never leaves your browser.")
    jd_text = st.text_area("💼 Paste the job description here", height=250, placeholder="Copy from LinkedIn, Naukri, or anywhere... 📝")

    mode = st.selectbox("🧠 Choose AI Analysis Mode", [
        "🧠 Full Resume Intelligence Report",
        "Brutal Resume Review",
        "Rewrite to Sound Results-Driven",
        "Optimize for ATS",
        "Generate Professional Summary",
        "Tailor Resume for Job Description",
        "Top 1% Candidate Benchmarking",
        "Generate Cover Letter",
        "Suggest Resume Format"
    ])

    section = st.selectbox("🔹 Focus on a specific resume section?", [
        "Entire Resume", "Professional Summary", "Experience", "Education", "Projects"
    ]) if mode == "Rewrite to Sound Results-Driven" else "Entire Resume"

    model_choice = st.radio(
        "Choose model:",
        ["Exaone (Deep & Accurate)", "Mistral (Fast & Light)"],
        index=0,
        horizontal=True
    )
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

        match_score = extract_score(result)
        global_score_match = re.search(r"Global Score\s*[:\-]\s*(\d{1,3})", result, re.IGNORECASE)
        global_percentile_match = re.search(r"Percentile Rank\s*[:\-]\s*Top\s*(\d{1,3})", result, re.IGNORECASE)

        global_score = int(global_score_match.group(1)) if global_score_match else None
        percentile = int(global_percentile_match.group(1)) if global_percentile_match else None

        if match_score or global_score:
            st.markdown("### 📊 Resume Evaluation Metrics")
            st.table({
                "Metric": ["Match Score", "Global Resume Score", "Percentile Rank"],
                "Value": [
                    f"{match_score}/100" if match_score else "N/A",
                    f"{global_score}/100" if global_score else "N/A",
                    f"Top {percentile}%" if percentile else "N/A"
                ]
            })

            fig = go.Figure(data=go.Heatmap(
                z=[[match_score, global_score, 90]],
                x=["Match Score", "Global Score", "ATS Score (est.)"],
                y=["Resume"],
                colorscale="RdYlGn",
                zmin=0,
                zmax=100,
                showscale=True
            ))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📈 Resume Score Progress Over Time")
        history = get_history()
        if history:
            df = pd.DataFrame(history)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            fig2 = go.Figure()
            if "match_score" in df:
                fig2.add_trace(go.Scatter(x=df["timestamp"], y=df["match_score"], mode='lines+markers', name="Match Score"))
            if "global_score" in df:
                fig2.add_trace(go.Scatter(x=df["timestamp"], y=df["global_score"], mode='lines+markers', name="Global Score"))
            st.plotly_chart(fig2, use_container_width=True)

    elif submitted:
        if not uploaded_file and not jd_text.strip():
            st.info("Upload your resume and paste a job description to begin.")
        elif not uploaded_file:
            st.warning("Please upload your resume.")
        elif not jd_text.strip():
            st.warning("Please paste a job description.")

# ------------ Phase 2: Explore Jobs ------------
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
