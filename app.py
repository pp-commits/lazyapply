import streamlit as st
from utils.resume_parser import parse_resume
from utils.matcher import get_match_feedback

st.set_page_config(page_title="LazyApply AI", layout="centered")

st.title("🤖 LazyApply AI — Your Job Buddy!")

st.markdown("Upload your resume and paste a job description to get match feedback.")

# Upload Resume
uploaded_file = st.file_uploader("📄 Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

# Paste JD
jd_text = st.text_area("💼 Paste the job description here", height=250)

# Submit Button
if uploaded_file and jd_text:
    resume_text = parse_resume(uploaded_file)
    
    if resume_text.strip():
        with st.spinner("🧠 Thinking..."):
            feedback = get_match_feedback(resume_text, jd_text)
        
        st.subheader("📊 Match Feedback")
        st.text_area("📝 AI Feedback", feedback, height=300)

        # Copy Button
        st.button("📋 Copy to Clipboard", on_click=lambda: st.session_state.update({"copied": True}))
        if st.session_state.get("copied"):
            st.success("Copied!")

        # Download Button
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
