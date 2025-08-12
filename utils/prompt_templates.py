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
        "Full Resume Intelligence Report": f"""
You are an expert resume analyst and recruiter, well-versed in hiring trends, ATS systems, and top-tier candidate benchmarks.

Given the following resume and job description, perform a complete multi-part evaluation and enhancement:

PART 1: Resume Critique
- Identify and explain weak areas in the resume
- Highlight vague statements, buzzwords, or lack of impact
- Point out any sections that need rewriting, expansion, or quantification
- Rate the overall effectiveness and clarity of the resume (out of 10)

PART 2: Role Alignment
- Compare resume to the job description
- Highlight 5 strong alignment areas
- List 5 key missing skills or phrases
- Assign a Match Score out of 100 and explain it, note that it is extremely important that the match score is consistent everytime and that it has to be accurate and precise, also it has to be brutally honest and not lenient

PART 3: ATS Optimization
- Rewrite the resume fully optimized for ATS
- Ensure relevant keywords are naturally included
- Use clean, single-column formatting with plain sections

 PART 4: Rewrite with Results
- Rephrase Experience using action verbs
- Focus on achievements and outcomes

 PART 5: Top 1% Benchmarking
- Describe what a top 1% resume for this role looks like
- Compare and list key improvements

 PART 6: Summary & Enhancement
- Write a 3-line professional summary

 PART 7: Resume Format Suggestion
- Suggest a modern, ATS-compatible format (Markdown or LaTeX)

 PART 8: Cover Letter Generator
- Generate a short, enthusiastic, job-specific letter

 PART 9: Final Analysis Summary
- Executive summary + a table of scores and metrics
- Conclude with: Ready to Apply, Needs Work, or Major Rewrite Needed

🌍 PART 10: Global Benchmarking Score
- Score out of 100 using global benchmarks
- Assign a percentile rank (e.g., Top 10%) and explain why

Resume:
{resume_text}

Job Description:
{jd_text if jd_text else '[No JD provided]'}
""",

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
