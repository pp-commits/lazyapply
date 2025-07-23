import streamlit as st
import requests
import re  # For extracting scores
from utils.prompt_templates import build_prompt  # ✅ New import

# 🔐 Load API key securely
TOGETHER_API_KEY = st.secrets["together"]["api_key"]

headers = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json"
}

# 🧠 Models
MAIN_MODEL = "lgai/exaone-3-5-32b-instruct"  # Deep analysis
LIGHT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # Fast summaries
API_URL = "https://api.together.xyz/v1/chat/completions"

print(f"[DEBUG] Primary model: {MAIN_MODEL}")
print(f"[DEBUG] Lightweight model: {LIGHT_MODEL}")

def call_together_api(prompt, model=MAIN_MODEL, temperature=0.7):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful resume evaluator AI assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": temperature
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.error(f"[API Error {response.status_code}]: {response.text}")
        return None

def extract_score(text):
    """Extracts a score (0–100) from model output."""
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
    """
    Full feedback with detailed prompt (used after user clicks 'Recalculate with full JD').
    Returns (feedback, score) or (feedback, None) on failure.
    """
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
    if result:
        score = extract_score(result)
        return result, score
    else:
        return "⚠️ API error or no result.", None

def get_batched_match_feedback(resume_text, jd_list):
    """
    Fast batch feedback using lighter model and job summaries.
    Each item returns a tuple: (feedback, score)
    """
    results = []

    for i, jd_text in enumerate(jd_list):
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

# ✅ New: Modular prompt handler
def get_custom_prompt_feedback(resume_text, jd_text=None, mode="Brutal Resume Review", section="Entire Resume", model=MAIN_MODEL):
    """
    Flexible prompt-based feedback engine.
    Supports modes like ATS, rewriting, summary, tailoring, etc.
    """
    prompt = build_prompt(resume_text, jd_text, mode=mode, section=section)
    result = call_together_api(prompt, model=model)

    if result:
        score = extract_score(result)
        return result, score
    else:
        return "⚠️ API error or no result.", None
