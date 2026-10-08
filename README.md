# 📄 Smart Resume Analyzer

An AI-powered web app that compares a candidate's resume (PDF) with a job description and produces a structured match report: score, verdict, matched and missing skills, strengths, and improvement suggestions.

🔗 **Live Demo:** https://smart-resume-analyzer--projectgit-by-prince.streamlit.app/



## ✨ Features

- Upload a resume in PDF format (text extracted with `pypdf`)
- Paste any job description
- AI analysis using Google Gemini (`gemini-3.8-flash`)
- Guaranteed valid JSON output using Gemini's native `response_schema`
- Dashboard with match score, verdict, skills gap, experience alignment, strengths and suggestions

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| PDF parsing | pypdf |
| AI model | Google Gemini 3.8 Flash |
| SDK | google-genai |
| Language | Python 3.9+ |

## 📊 Output Fields

`match_score`, `verdict`, `matched_skills`, `missing_skills`, `experience_alignment`, `strengths`, `improvement_suggestions`, `summary_feedback`

## 🚀 Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/prince8055-max/Smart-Resume-Analyzer-.git
cd Smart-Resume-Analyzer-

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key (get one at https://aistudio.google.com/apikey)
# Windows PowerShell:
$env:GEMINI_API_KEY="your-key-here"
# macOS / Linux:
# export GEMINI_API_KEY="your-key-here"

# 4. Run the app
python -m streamlit run app.py
```

You can also paste the API key into the app's sidebar instead of using an environment variable.

## 📁 Project Structure

```
Smart-Resume-Analyzer-/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── screenshots/        # README images
└── README.md
```

## 🔮 Future Scope

- OCR support for scanned PDFs
- Resume vs. multiple job descriptions ranking
- Downloadable PDF report
- Support for DOCX resumes

## 👤 Author

**Prince** — College Mini Project (AI & NLP)
