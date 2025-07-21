# 🤖 LazyApply AI — Outsmart the Resume Game

A ninja-grade tool to *slice through job descriptions* and give you AI-powered match feedback on your resume.

### ✨ What It Does
LazyApply helps job seekers instantly:
- 📄 Upload a resume (PDF or DOCX)
- 🧠 Paste or auto-fetch job descriptions
- 📊 Get AI-based match scores out of 100
- 🧩 See missing skills and how to improve
- ⬇️ Download or 📋 copy feedback
- 🔍 Explore real-time jobs from top tech companies (Razorpay, Freshworks, etc.)

---

### 💡 Why I Built It
Tired of blindly applying to jobs and not hearing back?  
LazyApply is a response to that — a resume/job description matcher powered by LLMs (like Mistral & LLaMA3), built to help *you* tailor your resume better, faster, smarter.

---

### 🛠️ Tech Stack

| Feature                | Stack Used                         |
|------------------------|-------------------------------------|
| Frontend               | Streamlit                          |
| Resume Parsing         | `pdfminer`, `docx2txt`              |
| LLM Integration        | `Ollama` (local Mistral/LLaMA3)     |
| Job Scraping           | `Playwright`, `requests`, `BeautifulSoup` |
| Match Logic            | Custom prompts + regex scoring     |
| Deployment             | Streamlit Community Cloud          |

---

### ⚠️ Challenges & Fixes

- **LLM Flakiness** → Switched models, added fallback logic
- **Score Parsing Fails** → Regex + tuple handling fixed
- **Job Boards Blocked** → Used Greenhouse APIs for job fetching
- **Deployment Woes** → Deployed on Streamlit Cloud with secret keys

---

### 📦 Local Setup

```bash
git clone https://github.com/pp-commits/lazyapply.git
cd lazyapply
pip install -r requirements.txt
ollama run mistral  # or llama3 if your system supports it
streamlit run app.py
