import streamlit as st
import requests
import re

TOGETHER_API_KEY = st.secrets["together"]["api_key"]

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

MAIN_MODEL = "lgai/exaone-3-5-32b-instruct"
LIGHT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
API_URL = "https://api.together.xyz/v1/chat/completions"

def call_together_api(prompt, model=MAIN_MODEL, temperature=0.7):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful resume evaluator AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "temperature": temperature
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.error(f"[API Error {response.status_code}]: {response.text}")
        return None

def extract_score(text):
    if not text:
        return None
    match = re.search(r"\b(\d{2,3})\s*out\s*of\s*100\b", text, re.IGNORECASE)
    if match:
        try:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
        except ValueError:
            return None
    return None

def get_match_feedback(resume_text, jd_text):
    prompt = f"""
You are a resume evaluator AI.
Compare the following resume with the job description and return:
- A brief feedback summary
- 3 highlighted matches
- 3 missing skills
-  Assign a Match Score out of 100 and explain it, note that it is extremely important that the match score is consistent everytime and that it has to be accurate and precise, also it has to be brutally honest and not lenient

Resume:
{resume_text}

Job Description:
{jd_text}
"""
    result = call_together_api(prompt)
    if result:
        score = extract_score(result)
        return result, score
    else:
        return "⚠️ API error or no result.", None

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
        result = call_together_api(prompt, model=LIGHT_MODEL)
        if result:
            score = extract_score(result)
            results.append((result, score))
        else:
            results.append(("⚠️ API error or no result.", None))
    return results

def get_custom_prompt_feedback(resume_text, jd_text, mode, section, model=MAIN_MODEL):
    from utils.prompt_templates import build_prompt
    prompt = build_prompt(resume_text, jd_text, mode)
    result = call_together_api(prompt, model=model)
    score = extract_score(result)
    return result, score

def get_full_resume_analysis(resume_text, jd_text):
    from utils.prompt_templates import build_prompt
    prompt = build_prompt(resume_text, jd_text, mode="Full Resume Intelligence Report")
    result = call_together_api(prompt, model=MAIN_MODEL)
    score = extract_score(result)
    return result, score
