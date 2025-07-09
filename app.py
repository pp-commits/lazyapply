import streamlit as st
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback
from utils.history import save_match, get_history
from utils.job_scraper.razorpay import fetch_jobs  # ✅ Razorpay fetch function

st.set_page_config(page_title="LazyApply AI", layout="centered")

st.title("🤖 LazyApply AI — Your Job Buddy!")

tab1, tab2 = st.tabs(["📄 Match Resume", "🧭 Explore Jobs"])

# ---------------------- Phase 1 ----------------------
with tab1:
    st.markdown("Upload your resume and paste a job description to get match feedback.")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("💼 Paste the job description here", height=250)

    if uploaded_file and jd_text:
        resume_text = parse_resume(uploaded_file)

        if resume_text.strip():
            with st.spinner("🧠 Thinking..."):
                feedback = get_match_feedback(resume_text, jd_text)

            st.subheader("📊 Match Feedback")
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

# ---------------------- Phase 2 ----------------------
with tab2:
    st.markdown("🧠 Showing engineering roles at **Razorpay** via official job board")
    jobs = fetch_jobs(limit=10, keyword="engineering")

    if isinstance(jobs, str):
        st.error(jobs)
    elif not jobs:
        st.warning("No engineering roles found right now.")
    else:
        for job in jobs:
            with st.expander(f"🔧 {job['title']} – {job['location']}"):
                st.markdown(f"**Company**: {job['company']}")
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
