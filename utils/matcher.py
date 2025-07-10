

import ollama  

def get_match_feedback(resume_text, jd_text):
    prompt = f"""
You are a top-tier career strategist, resume analyst, and ATS (Applicant Tracking System) optimization expert with deep knowledge of hiring trends across various industries.

Your task is to evaluate how well the resume below aligns with the provided job description. Analyze based on:

ATS compatibility

Keyword relevance

Role-specific skills (both technical and soft)

Action verbs and measurable achievements

Industry-specific expectations

Formatting preferences that influence recruiter decisions

Then, provide a detailed response with:

Match Score (out of 100) based on relevance to the job description and ATS compatibility.

Top 5 Missing or Weak Areas in the resume that reduce the chances of selection (these could be skills, experience, or alignment issues).

Suggested Resume Bullet Points (max 5), written in a professional tone with strong verbs and quantifiable results, that can be added to improve the resume's relevance. Also mention exactly what in the given resume needs to be edited or replaced with suggestions.

Optional ATS Optimization Tips (1–2 lines) if applicable.

Resume:
{resume_text}

Job Description:
{jd_text}

Respond strictly in the following format:
Match Score: <score>/100

Top 3 Gaps or Mismatches:
1. ...
2. ...
3. ...

Suggested Resume Bullet Points:
- ...
- ...

ATS Optimization Tip (Optional):
...

"""

    response = ollama.chat(
        model='llama3',  # Or use 'mistral' or another model you installed
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content']
