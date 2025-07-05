

import ollama  

def get_match_feedback(resume_text, jd_text):
    prompt = f"""
You are a career coach and job-matching expert.

Given the resume and job description below, rate how well the resume matches the job out of 100. 
List the top 3 missing skills and suggest 2 resume bullet points that could be added to improve the match.

Resume:
{resume_text}

Job Description:
{jd_text}

Respond in this format:
Match Score: <score>/100

Missing Skills:
1. ...
2. ...
3. ...

Suggested Bullet Points:
- ...
- ...
"""

    response = ollama.chat(
        model='llama3',  # Or use 'mistral' or another model you installed
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content']
