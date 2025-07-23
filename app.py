import streamlit as st
import requests
import time
import re
from io import BytesIO
from docx import Document

from utils.resume_parser import parse_resume
from utils.matcher import (
    get_match_feedback,
    get_batched_match_feedback,
    get_custom_prompt_feedback
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
st.title("🤖 LazyApply AI — Your Job Buddy!")

tab1, tab2 = st.tabs(["📄 Match Resume", "𞳻 Explore Jobs"])

# ------------ Phase 1: Resume Matching ------------
with tab1:
    st.markdown("Upload your resume and paste a job description to get match feedback.")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("💼 Paste the job description here", height=250)

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
    submitted = st.button("🚀 Generate Feedback")

    if submitted and resume_text and resume_text.strip() and jd_text.strip():
        key_hash = hash(resume_text + jd_text + mode + section + chosen_model)

        if st.session_state.get("input_hash") != key_hash:
            with st.spinner("🔬 Processing your resume..."):
                
                if mode == "Tailor Resume for Job Description" and not jd_text:
                    st.warning("This mode works best with a job description pasted above.")
                if mode == "🧠 Full Resume Intelligence Report":
                    from utils.matcher import get_full_resume_analysis
                    result, score = get_full_resume_analysis(resume_text, jd_text)
                else:
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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.session_state["copied"] = True
            if st.session_state.get("copied"):
                st.success("Copied!")

        with col2:
            st.download_button(
                label="⬇️ Download as .docx",
                data=generate_docx(result),
                file_name="lazyapply_output.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        with st.expander("📄 View My Feedback History"):
            history = get_history()
            if not history:
                st.info("No past matches found.")
            else:
                for i, entry in enumerate(history[:5]):
                    st.markdown(f"**{entry['timestamp']}**")
                    st.code(entry['feedback'], language='markdown')

        if mode == "Tailor Resume for Job Description":
            all_jobs = st.session_state["job_cache"]
            flat_jobs = [{"company": comp, **job} for comp, jobs in all_jobs.items() for job in jobs]
            summaries = [job["summary"] for job in flat_jobs]
            feedbacks = get_batched_match_feedback(resume_text, summaries)

            scored_jobs = []
            for job, feedback in zip(flat_jobs, feedbacks):
                if isinstance(feedback, tuple):
                    feedback_text = feedback[0]
                    match = re.search(r'(\d{1,3})\s*(?:/|out of)\s*100', feedback_text, re.IGNORECASE)
                    if match:
                        score_val = int(match.group(1))
                        scored_jobs.append({
                            "company": job["company"],
                            "title": job["title"],
                            "location": job["location"],
                            "score": score_val,
                            "link": job["link"],
                            "summary": job["summary"]
                        })

            if scored_jobs:
                st.markdown("---")
                st.subheader("📌 Similar Jobs You May Like")
                for job in sorted(scored_jobs, key=lambda x: x["score"], reverse=True)[:5]:
                    with st.expander(f"{job['title']} at {job['company']} — Match Score: {job['score']}%"):
                        st.markdown(f"**Location**: {job['location']}")
                        st.markdown(f"**Apply**: [Click here]({job['link']})")
                        if st.button(f"🔍 Recalculate with Full JD for '{job['title']}'", key=f"recalc_{job['title']}"):
                            with st.spinner("Fetching full JD and rescoring..."):
                                full_jd = fetch_full_job_description(job["link"])
                                if full_jd:
                                    updated = get_match_feedback(resume_text, full_jd)
                                    updated_str = str(updated[0]) if isinstance(updated, tuple) else str(updated)
                                    st.text_area("📊 Updated Feedback", updated_str, height=300)
                                else:
                                    st.error("Could not fetch full job description.")
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
