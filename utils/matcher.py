import streamlit as st
import requests

# 🔐 Load Together API key from Streamlit secrets
TOGETHER_API_KEY = st.secrets["together"]["api_key"]

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# 🔧 Model configuration
MAIN_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"  # For detailed matching
LIGHT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"           # For similar jobs
API_URL = "https://api.together.xyz/v1/chat/completions"

print(f"[DEBUG] Primary model: {MAIN_MODEL}")
print(f"[DEBUG] Lightweight model: {LIGHT_MODEL}")

def call_together_api(prompt, model=MAIN_MODEL):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful resume evaluator AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.7
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
        return "⚠️ API call failed."

def get_match_feedback(resume_text, jd_text):
    prompt = f"""
You are a resume evaluator AI.
Compare the following resume with the job description and return:
- A brief feedback summary
- 3 highlighted matches
- 3 missing skills
- A match score out of 100

Resume:
{resume_text}

Job Description:
{jd_text}
"""
    result = call_together_api(prompt)

    # Try to extract score
    score = None
    for line in result.splitlines():
        if "Match Score" in line:
            try:
                score = int(line.split(":")[1].split("/")[0].strip("* "))
            except:
                pass

    return (result, score) if score else result

def get_batched_match_feedback(resume_text, jd_list):
    results = []
    for jd_text in jd_list:
        prompt = f"""
Compare the following resume with the job summary.
Return a brief reasoning and a match score out of 100.

Resume:
{resume_text}

Job Summary:
{jd_text}
"""
        # Use lightweight model for batch
        result = call_together_api(prompt, model=LIGHT_MODEL)
        results.append(result)
    return results
