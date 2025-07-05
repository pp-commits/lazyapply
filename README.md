# 🥷 LazyApply AI — Outsmart Job Portals Like a Ninja

LazyApply AI is your silent career sidekick — a sleek, no-frills agent that **analyzes your resume**, **reads job descriptions**, and gives you laser-sharp feedback on how well you match... all **without OpenAI API fees**.

No more guessing. Just upload your resume, paste a JD, and get:
- ✅ A Match Score (out of 100)
- 🧠 Top 3 Missing Skills
- 🧾 Bullet Points to Add
- 💾 Downloadable Reports
- 📋 Copyable Results

---

### ⚙️ Tech Stack

| Part | Stack |
|------|-------|
| 🖥️ Frontend | Streamlit |
| 📄 Resume Parsing | `pdfplumber`, `python-docx` |
| 🧠 LLM Engine | [LLaMA 3 via Ollama](https://ollama.com) |
| 🔐 Env Management | `python-dotenv` |
| 📦 Extras | `ollama`, `streamlit` |

---

### 🧪 How It Works

1. Upload your resume (`.pdf` or `.docx`)
2. Paste any job description
3. AI compares, scores, and suggests bullet points
4. You copy/download and apply like a boss

---

### 🚀 Run It Locally

> No API key needed. All AI runs **locally** on your machine!

#### 🧰 Setup

```bash
git clone https://github.com/pp-commits/lazyapply.git
cd lazyapply
pip install -r requirements.txt
