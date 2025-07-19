import ollama
import re

def get_match_feedback(resume_text, jd_text):
    prompt = f"""
You are a top-tier resume and job-match analyst.

Resume:
{resume_text}

Job Description:
{jd_text}

Give output strictly in this format:
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
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response['message']['content']
    match = re.search(r"Match Score:\s*\**\s*(\d{1,3})", content)
    score = int(match.group(1)) if match else 0
    return content, score

def get_batched_match_feedback(resume_text, jobs):
    import ollama
    import re

    prompt = f"""
You are a resume-job match scoring system. A resume is provided below. Then you will get multiple job summaries.

For each job summary, return a line in the following format:
Job <number> Match Score: <score>/100

Only output these lines.

Resume:
{resume_text}

"""

    for idx, summary in enumerate(jobs, start=1):
        prompt += f"Job {idx} Summary:\n{summary}\n\n"

    response = ollama.chat(
        model='llama3',
        messages=[{"role": "user", "content": prompt}]
    )

    content = response['message']['content']
    lines = content.strip().splitlines()

    results = []
    for i, line in enumerate(lines):
        try:
            match = re.search(r"Job\s*(\d+)\s*Match Score:\s*(\d{1,3})\/100", line)
            if match:
                results.append({
                    "job_index": int(match.group(1)) - 1,  # index for matching job later
                    "score": int(match.group(2)),
                    "feedback": line
                })
            else:
                results.append({
                    "job_index": i,
                    "score": 0,
                    "feedback": f"Job {i+1} Match Score: 0/100 (couldn't parse)"
                })
        except Exception as e:
            results.append({
                "job_index": i,
                "score": 0,
                "feedback": f"Job {i+1} Failed: {str(e)}"
            })

    return results
