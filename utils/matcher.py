import streamlit as st
import requests

# 🔐 Securely load API key from Streamlit secrets
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

# Define headers using the secret key
headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# Sample function to call Together.ai for inference
def get_model_response(prompt, model="togethercomputer/llama-2-7b-chat"):
    api_url = "https://api.together.xyz/v1/completions"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0.7
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json().get("choices")[0].get("text", "").strip()
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
        return None

# Example Streamlit UI
def main():
    st.title("🧠 JobFit AI - Resume + JD Matcher")

    resume_text = st.text_area("Paste your resume here:", height=200)
    jd_text = st.text_area("Paste the job description here:", height=200)

    if st.button("Analyze Fit"):
        with st.spinner("Analyzing..."):
            prompt = f"""You are an AI assistant that evaluates resume and job description match.
Return a score (out of 100) and highlight matching and missing skills.
Resume: 
{resume_text}

Job Description:
{jd_text}
"""
            result = get_model_response(prompt)
            if result:
                st.success("Result:")
                st.markdown(result)

if __name__ == "__main__":
    main()
