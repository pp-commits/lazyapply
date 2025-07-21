import streamlit as st
import requests

# 🔐 Load Together API key from Streamlit secrets
TOGETHER_API_KEY = st.secrets["together"]["api_key"]

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# ✅ Updated to chat completions endpoint
API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
print(f"[DEBUG] Using model: {MODEL_NAME}")

def call_together_api(prompt, model=MODEL_NAME):
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
Return a brief feedback and a Match Score (out of 100).

Resume:
{resume_text}

Job Summary:
{jd_text}
"""
        result = call_together_api(prompt)
        results.append(result)
    return results
