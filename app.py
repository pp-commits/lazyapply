import streamlit as st
import requests
import time
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback, get_batched_match_feedback
from utils.job_scraper.common import fetch_greenhouse_jobs, fetch_full_job_description

# ------------ Config for Supported Companies ------------
SUPPORTED_COMPANIES = {
    "Razorpay": "razorpaysoftwareprivatelimited",
    "Postman": "postman",
    "Turing": "turing",
    "Groww": "groww"
}

# ------------ Cache Greenhouse Jobs Initially ------------
if "job_cache" not in st.session_state:
    all_jobs = {}
    for comp_name, slug in SUPPORTED_COMPANIES.items():
        jobs = fetch_greenhouse_jobs(slug, limit=3, keyword="engineering")
        all_jobs[comp_name] = jobs
    st.session_state["job_cache"] = all_jobs

st.set_page_config(page_title="LazyApply AI", layout="centered")
st.title("🤖 LazyApply AI — Your Job Buddy!")

tab1, tab2 = st.tabs(["📄 Match Resume", "🗭 Explore Jobs"])

# ------------ Phase 1: Resume Matching ------------
with tab1:
    st.markdown("Upload your resume and paste a job description to get match feedback.")
    uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])
    jd_text = st.text_area("💼 Paste the job description here", height=250)

    resume_text = parse_resume(uploaded_file) if uploaded_file else None

    if resume_text and jd_text and resume_text.strip():
        input_hash = hash(resume_text + jd_text)

        # Trigger AI only if content changed
        if st.session_state.get("input_hash") != input_hash:
            progress = st.progress(0)
            status_placeholder = st.empty()
            feedback_placeholder = st.empty()

            status_msgs = ["🔍 Analyzing Resume", "📄 Parsing JD", "⚙️ Matching Skills", "🧠 Generating Insights"]
            for i, msg in enumerate(status_msgs):
                status_placeholder.markdown(f"**{msg}...**")
                progress.progress((i + 1) * 20)
                time.sleep(0.7)

            real_feedback = get_match_feedback(resume_text, jd_text)

            progress.progress(100)
            status_placeholder.markdown("✅ Done.")

            st.session_state["input_hash"] = input_hash
            st.session_state["feedback"] = real_feedback
            st.session_state["copied"] = False
        else:
            real_feedback = st.session_state["feedback"]

        st.text_area("📊 AI Feedback", real_feedback if isinstance(real_feedback, str) else real_feedback[0], height=300)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.session_state["copied"] = True
            if st.session_state.get("copied"):
                st.success("Copied!")

        with col2:
            st.download_button(
                label="⬇️ Download Report",
                data=real_feedback[0].encode("utf-8") if isinstance(real_feedback, tuple) else real_feedback.encode("utf-8"),
                file_name="match_feedback.txt",
                mime="text/plain"
            )

        # Batch match with cached jobs
        if "similar_jobs" not in st.session_state or st.session_state["input_hash"] != input_hash:
            all_jobs = st.session_state["job_cache"]
            flat_jobs = [{"company": comp, **job} for comp, jobs in all_jobs.items() for job in jobs]
            summaries = [job["summary"] for job in flat_jobs]
            feedbacks = get_batched_match_feedback(resume_text, summaries)

            scored_jobs = []
            debug_logs = []

            for idx, (job, feedback) in enumerate(zip(flat_jobs, feedbacks)):
                try:
                    lines = feedback.splitlines() if isinstance(feedback, str) else []
                    match_line = next((line for line in lines if "Match Score:" in line), None)
                    if match_line:
                        score_val = int(match_line.split(":")[1].split("/")[0].strip("* "))
                        scored_jobs.append({
                            "company": job["company"],
                            "title": job["title"],
                            "location": job["location"],
                            "score": score_val,
                            "link": job["link"],
                            "summary": job["summary"]
                        })
                    else:
                        debug_logs.append(f"Job {idx+1}: Match Score not found.")
                except Exception as e:
                    debug_logs.append(f"Job {idx+1} Error: {str(e)}")

            st.session_state["similar_jobs"] = scored_jobs
            st.session_state["debug_logs"] = debug_logs
        else:
            scored_jobs = st.session_state["similar_jobs"]
            debug_logs = st.session_state.get("debug_logs", [])

        st.markdown("---")
        st.subheader("📌 Similar Jobs You May Like")

        if scored_jobs:
            sorted_jobs = sorted(scored_jobs, key=lambda x: x["score"], reverse=True)[:5]
            for job in sorted_jobs:
                with st.expander(f"{job['title']} at {job['company']} — Match Score: {job['score']}%"):
                    st.markdown(f"**Location**: {job['location']}")
                    st.markdown(f"**Apply**: [Click here]({job['link']})")

                    if st.button(f"🔍 Recalculate with Full JD for '{job['title']}'", key=f"recalc_{job['title']}"):
                        with st.spinner("Fetching full JD and rescoring..."):
                            full_jd = fetch_full_job_description(job["link"])
                            if full_jd:
                                new_feedback, new_score = get_match_feedback(resume_text, full_jd)
                                st.success(f"✅ Updated Match Score: {new_score}/100")
                                st.text_area("📊 Updated Feedback", new_feedback, height=300)
                            else:
                                st.error("⚠️ Could not fetch full job description.")
        else:
            st.warning("No valid scores returned from LLM.")

        if debug_logs:
            st.markdown("**Debug Info:**")
            for log in debug_logs:
                st.markdown(f"- {log}")

    elif not uploaded_file:
        st.info("Please upload a resume.")
    elif not jd_text:
        st.info("Please paste a job description.")
    else:
        st.warning("Resume text could not be extracted.")

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
