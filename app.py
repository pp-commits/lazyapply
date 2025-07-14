import streamlit as st
import time
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

status_steps = ["🔍 Scanning Resume", "🧠 Analyzing JD", "📊 Matching Skills", "📚 Compiling Feedback", "🎯 Finalizing Result"]

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
            st.subheader("📊 Match Feedback")
            progress_bar = st.progress(0)
            status_placeholder = st.empty()

            # Simulate step-by-step loading
            step_count = len(status_steps)
            for i, step in enumerate(status_steps):
                progress_bar.progress((i + 1) / step_count)
                status_placeholder.markdown(step)
                time.sleep(0.6)  # adjust for pacing

            # Final processing (simulate real load if needed)
            feedback = get_match_feedback(resume_text, jd_text)

            # Clear loading elements
            progress_bar.empty()
            status_placeholder.empty()

            # Show results
            st.text_area("📝 AI Feedback", feedback, height=300)

            if st.button("📋 Copy to Clipboard"):
                st.session_state["copied"] = True
            if st.session_state.get("copied"):
                st.success("Copied!")

            st.download_button(
                label="⬇️ Download Report",
                data=feedback,
                file_name="match_feedback.txt",
                mime="text/plain"
            )
        else:
            st.warning("Resume text could not be extracted.")
    else:
        st.info("Please upload a resume and paste a job description.")

# ------------ Phase 2: Explore Engineering Jobs ------------
with tab2:
    st.markdown("🧠 Select a company to explore engineering jobs:")

    selected_company = st.selectbox("🏢 Choose a company", list(SUPPORTED_COMPANIES.keys()))
    company_slug = SUPPORTED_COMPANIES[selected_company]

    jobs = fetch_greenhouse_jobs(company_slug, limit=10, keyword="engineering")

    if isinstance(jobs, str):
        st.error(jobs)
    elif not jobs:
        st.warning("No engineering roles found right now.")
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

                        # Begin Loading
                        progress_bar = st.progress(0)
                        status_placeholder = st.empty()
                        for i, step in enumerate(status_steps):
                            progress_bar.progress((i + 1) / step_count)
                            status_placeholder.markdown(step)
                            time.sleep(0.6)

                        feedback = get_match_feedback(resume_text, job['summary'])

                        # Clear loading
                        progress_bar.empty()
                        status_placeholder.empty()

                        st.success("✅ Match completed!")
                        st.text_area("📊 Feedback", feedback, height=300)
                else:
                    st.info("Upload resume in Tab 1 to enable matching.")
