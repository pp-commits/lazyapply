import streamlit as st
import requests
import time
import random
import threading
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback
from utils.job_scraper.common import fetch_greenhouse_jobs

# ------------ Config for Supported Companies ------------
SUPPORTED_COMPANIES = {
    "Razorpay": "razorpaysoftwareprivatelimited",
    "Postman": "postman",
    "Turing": "turing",
    "Groww": "groww"
}

# ------------ Streamlit UI ------------
st.set_page_config(page_title="LazyApply AI", layout="centered")
st.title("🤖 LazyApply AI — Your Job Buddy!")

tab1, tab2 = st.tabs(["📄 Match Resume", "🧭 Explore Jobs"])

# ------------ Phase 1: Resume Matching ------------
with tab1:
    st.markdown("Upload your resume and paste a job description to get match feedback.")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("💼 Paste the job description here", height=250)

    if uploaded_file and jd_text:
        resume_text = parse_resume(uploaded_file)
        if resume_text.strip():
            progress = st.progress(0)
            status_placeholder = st.empty()
            score_placeholder = st.empty()
            feedback_placeholder = st.empty()

            # Sequential steps with status
            status_msgs = ["🔍 Analyzing Resume", "📄 Parsing JD", "⚙️ Matching Skills", "🧠 Generating Insights"]
            for i, msg in enumerate(status_msgs):
                status_placeholder.markdown(f"**{msg}...**")
                progress.progress((i + 1) * 20)
                time.sleep(0.7)

            # Score animation (main thread)
            for _ in range(20):  # approx 2 seconds
                score = random.randint(1, 99)
                score_placeholder.markdown(f"🎯 Estimated Match Score: **{score}%**")
                time.sleep(0.1)

            # Final feedback (blocking call)
            real_feedback = get_match_feedback(resume_text, jd_text)

            # Extract score from feedback if available
            #final_score = real_feedback.split("Match Score:")[-1].split("%")[0].strip() if "Match Score:" in real_feedback else "85"
            #score_placeholder.markdown(f"✅ Final Match Score: **{final_score}%**")

            progress.progress(100)
            status_placeholder.markdown("✅ Done.")

            feedback_placeholder.text_area("📊 AI Feedback", real_feedback, height=300)

            if st.button("📋 Copy to Clipboard"):
                st.session_state["copied"] = True
            if st.session_state.get("copied"):
                st.success("Copied!")

            st.download_button(
                label="⬇️ Download Report",
                data=real_feedback,
                file_name="match_feedback.txt",
                mime="text/plain"
            )
        else:
            st.warning("Resume text could not be extracted.")
    else:
        st.info("Please upload a resume and paste a job description.")


# ------------ Phase 2: Explore Jobs with Dynamic Search ------------
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
                            st.text_area("📊 Feedback", feedback, height=300)
                    else:
                        st.info("Upload resume in Tab 1 to enable matching.")
    else:
        st.info("Please enter a keyword to search job roles.")

