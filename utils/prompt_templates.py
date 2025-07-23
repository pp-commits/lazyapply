import re

def extract_job_title(jd_text):
    if not jd_text:
        return "the target role"
    title_match = re.search(r"(?i)(?:role|title)\s*[:\-]\s*(.+)", jd_text)
    if title_match:
        return title_match.group(1).strip().split('\n')[0]
    first_line = jd_text.strip().split('\n')[0]
    return first_line if len(first_line) < 80 else "the target role"

def extract_section(resume, section_name):
    pattern = rf"{section_name}.*?(?=\n[A-Z][a-z]+|\Z)"
    match = re.search(pattern, resume, re.DOTALL | re.IGNORECASE)
    return match.group(0).strip() if match else resume

def build_prompt(resume_text, jd_text=None, mode="Brutal Resume Review", section="Entire Resume"):
    job_title = extract_job_title(jd_text)

    if section != "Entire Resume":
        resume_text = extract_section(resume_text, section)

    prompt_sections = {
        "Brutal Resume Review": f"""
You are a seasoned recruiter reviewing the resume below. Be brutally honest.
- Highlight vague statements, weak points, overused buzzwords, or missing metrics.
- Give direct, specific feedback.

Resume:
{resume_text}
""",

        "Rewrite to Sound Results-Driven": f"""
Rewrite this resume to be results-driven and achievement-oriented.
Use strong action verbs and quantify impact where possible.

Resume:
{resume_text}
""",

        "Optimize for ATS": f"""
You are an ATS optimization expert.

Update this resume for the role of "{job_title}" to:
- Include industry-specific keywords
- Improve ATS compatibility
- Use a clean single-column layout with structured headings

Resume:
{resume_text}
""",

        "Generate Professional Summary": f"""
Write a 3-line professional summary that hooks a recruiter in 10 seconds.
Focus on value, clarity, and fit for the target role.

Resume:
{resume_text}
""",

        "Tailor Resume for Job Description": f"""
Tailor this resume for the following job. Highlight matches and rephrase sections to align with the job language.

Resume:
{resume_text}

Job Description:
{jd_text if jd_text else '[No JD provided]'}
""",

        "Top 1% Candidate Benchmarking": f"""
Act like a hiring manager. Compare this resume to the job below.
- What would a top 1% candidate include?
- What should be improved?

Resume:
{resume_text}

Job Description:
{jd_text if jd_text else '[No JD provided]'}
""",

        "Generate Cover Letter": f"""
Write a short (under 200 words), personalized cover letter based on this resume and job description.
Make it enthusiastic, aligned, and recruiter-friendly.

Resume:
{resume_text}

Job Description:
{jd_text if jd_text else '[No JD provided]'}
""",

        "Suggest Resume Format": f"""
Suggest a clean, modern, ATS-friendly resume format.
Use Markdown or LaTeX. Avoid columns/graphics. Include standard sections like Summary, Skills, Experience, Education, Projects.

Resume:
{resume_text}
"""
    }

    return prompt_sections.get(mode, f"Invalid mode: {mode}")
