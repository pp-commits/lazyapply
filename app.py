import streamlit as st
import requests
import time
import random
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback, get_batched_match_feedback
from utils.job_scraper.common import fetch_greenhouse_jobs

# ------------ Config for Supported Companies ------------
SUPPORTED_COMPANIES = {
    "Razorpay": "razorpaysoftwareprivatelimited",
    "Postman": "postman",
    "Turing": "turing",
    "Groww": "groww"
}

# ------------ Phase 2: Explore Jobs Logic FIRST (but visually second) ------------
if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

# ------------ Streamlit UI ------------
st.set_page_config(page_title="LazyApply AI", layout="centered")
st.title("🤖 LazyApply AI — Your Job Buddy!")

tab1, tab2 = st.tabs(["📄 Match Resume", "🧭 Explore Jobs"])

# ------------ Phase 1: Resume Matching ------------
with tab1:
    st.markdown("Upload your resume and paste a job description to get match feedback.")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("💼 Paste the job description here", height=250)

    if uploaded_file:
        resume_text = parse_resume(uploaded_file)
    else:
        resume_text = None

    if resume_text and jd_text:
        if resume_text.strip():
            progress = st.progress(0)
            status_placeholder = st.empty()
            feedback_placeholder = st.empty()

            status_msgs = ["🔍 Analyzing Resume", "📄 Parsing JD", "⚙️ Matching Skills", "🧠 Generating Insights"]
            for i, msg in enumerate(status_msgs):
                status_placeholder.markdown(f"**{msg}...**")
                progress.progress((i + 1) * 20)
                time.sleep(0.7)

            # Final feedback
            real_feedback = get_match_feedback(resume_text, jd_text)
            progress.progress(100)
            status_placeholder.markdown("✅ Done.")
            feedback_placeholder.text_area("📊 AI Feedback", real_feedback if isinstance(real_feedback, str) else real_feedback[0], height=300)

            if st.button("📋 Copy to Clipboard"):
                st.session_state["copied"] = True
            if st.session_state.get("copied"):
                st.success("Copied!")

            st.download_button(
                label="⬇️ Download Report",
                data=real_feedback[0].encode("utf-8") if isinstance(real_feedback, tuple) else real_feedback.encode("utf-8"),
                file_name="match_feedback.txt",
                mime="text/plain"
            )

            # ---------- Show Similar Jobs with Scores ----------
            st.markdown("---")
            st.subheader("📌 Similar Jobs You May Like")

            all_jobs = st.session_state["job_cache"]
            flat_jobs = []
            for comp_name, job_list in all_jobs.items():
                for job in job_list:
                    flat_jobs.append({"company": comp_name, **job})

            summaries = [job["summary"] for job in flat_jobs]
            feedbacks = get_batched_match_feedback(resume_text, summaries)

            scored_jobs = []
            debug_logs = []

            for idx, (job, feedback) in enumerate(zip(flat_jobs, feedbacks)):
                try:
                    if not isinstance(feedback, str):
                        feedback = feedback.get("feedback", "")

                    lines = feedback.splitlines()
                    match_line = next((line for line in lines if "Match Score:" in line), None)

                    if match_line:
                        score_val = int(match_line.split(":")[1].split("/")[0].strip("* "))
                        scored_jobs.append({
                            "company": job["company"],
                            "title": job["title"],
                            "location": job["location"],
                            "score": score_val,
                            "link": job["link"]
                        })
                    else:
                        debug_logs.append(f"Job {idx+1}: Match Score not found in response")
                except Exception as e:
                    debug_logs.append(f"Job {idx+1} Failed: {str(e)}")

            if scored_jobs:
                sorted_jobs = sorted(scored_jobs, key=lambda x: x["score"], reverse=True)[:5]
                for job in sorted_jobs:
                    with st.expander(f"{job['title']} at {job['company']} — Match Score: {job['score']}%"):
                        st.markdown(f"**Location**: {job['location']}")
                        st.markdown(f"**Apply**: [Click here]({job['link']})")
            else:
                st.warning("No valid scores returned from LLM.")

            if debug_logs:
                st.markdown("**Debug Info:**")
                for log in debug_logs:
                    st.markdown(f"- {log}")
        else:
            st.warning("Resume text could not be extracted.")
    elif not uploaded_file:
        st.info("Please upload a resume.")
    else:
        st.info("Please paste a job description.")

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
                    st.markdown(f"**Summary**:\n\n{job['summary']}")

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
