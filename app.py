"""
Smart Resume Analyzer - AI + NLP mini-project
Stack: Streamlit + pypdf + Google GenAI SDK (gemini-2.5-flash)

Run:  streamlit run app.py
"""

import json
import os

import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
MODEL_NAME = "gemini-2.5-flash"
MAX_CHARS = 30_000  # safety cap on text sent to the model

st.set_page_config(
    page_title="Smart Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Structured-output schema (native Gemini response_schema)
# --------------------------------------------------------------------------- #
STRING_ARRAY = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(type=types.Type.STRING),
)

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "match_score": types.Schema(
            type=types.Type.INTEGER,
            minimum=0,
            maximum=100,
            description="Overall resume-to-JD match score from 0 to 100.",
        ),
        "verdict": types.Schema(
            type=types.Type.STRING,
            enum=["Strong Match", "Moderate Match", "Weak Match"],
            description="Overall verdict for the candidate.",
        ),
        "matched_skills": STRING_ARRAY,
        "missing_skills": STRING_ARRAY,
        "experience_alignment": types.Schema(
            type=types.Type.STRING,
            description="Short summary of how the candidate's experience aligns with the role.",
        ),
        "strengths": STRING_ARRAY,
        "improvement_suggestions": STRING_ARRAY,
        "summary_feedback": types.Schema(
            type=types.Type.STRING,
            description="Overall feedback in 2-3 sentences.",
        ),
    },
    required=[
        "match_score",
        "verdict",
        "matched_skills",
        "missing_skills",
        "experience_alignment",
        "strengths",
        "improvement_suggestions",
        "summary_feedback",
    ],
    property_ordering=[
        "match_score",
        "verdict",
        "matched_skills",
        "missing_skills",
        "experience_alignment",
        "strengths",
        "improvement_suggestions",
        "summary_feedback",
    ],
)

SYSTEM_INSTRUCTION = (
    "You are an expert technical recruiter and ATS (Applicant Tracking System) analyst. "
    "Compare the candidate's resume against the target job description objectively. "
    "Base every claim ONLY on evidence in the resume text; never invent skills or experience. "
    "Scoring guide: 75-100 = 'Strong Match', 50-74 = 'Moderate Match', 0-49 = 'Weak Match'. "
    "Keep list items short and specific. The summary_feedback must be 2-3 sentences."
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def extract_text_from_pdf(uploaded_file) -> str:
    """Extract raw text from every page of an uploaded PDF using pypdf."""
    reader = PdfReader(uploaded_file)

    if reader.is_encrypted:
        try:
            reader.decrypt("")  # try empty password
        except Exception:
            raise ValueError("The PDF is password-protected and cannot be read.")

    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def get_api_key(sidebar_value: str) -> str:
    """Resolve API key: sidebar input > env var > Streamlit secrets."""
    if sidebar_value:
        return sidebar_value.strip()
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def analyze_resume(api_key: str, resume_text: str, job_description: str) -> dict:
    """Call Gemini with a response_schema and return the parsed JSON dict."""
    client = genai.Client(api_key=api_key)

    prompt = (
        "Analyze the following resume against the job description.\n\n"
        "=== JOB DESCRIPTION ===\n"
        f"{job_description[:MAX_CHARS]}\n\n"
        "=== RESUME ===\n"
        f"{resume_text[:MAX_CHARS]}\n"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.2,
        ),
    )

    # With response_schema the output is raw JSON - no markdown stripping needed.
    data = json.loads(response.text)
    data["match_score"] = max(0, min(100, int(data.get("match_score", 0))))
    return data


def render_bullets(items: list[str], empty_msg: str = "Nothing to show.") -> None:
    if not items:
        st.caption(empty_msg)
        return
    st.markdown("\n".join(f"- {item}" for item in items))


def render_results(result: dict) -> None:
    score = result["match_score"]
    verdict = result["verdict"]
    matched = result["matched_skills"]
    missing = result["missing_skills"]

    st.divider()
    st.subheader("📊 Analysis Dashboard")

    # --- KPI row ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Match Score", f"{score}/100")
    m2.metric("Verdict", verdict)
    m3.metric("Skills Matched", len(matched))
    m4.metric("Skills Missing", len(missing))
    st.progress(score / 100, text=f"Overall fit: {score}%")

    # --- Verdict banner ---
    if verdict == "Strong Match":
        st.success(f"✅ {verdict}: {result['summary_feedback']}")
    elif verdict == "Moderate Match":
        st.warning(f"⚠️ {verdict}: {result['summary_feedback']}")
    else:
        st.error(f"❌ {verdict}: {result['summary_feedback']}")

    # --- Skills ---
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### ✅ Matched Skills")
            render_bullets(matched, "No matched skills found.")
    with col_b:
        with st.container(border=True):
            st.markdown("#### ❗ Missing Skills")
            render_bullets(missing, "No missing skills - great coverage!")

    # --- Experience alignment ---
    st.markdown("#### 💼 Experience Alignment")
    st.info(result["experience_alignment"])

    # --- Strengths & suggestions ---
    col_c, col_d = st.columns(2)
    with col_c:
        with st.container(border=True):
            st.markdown("#### 💪 Strengths")
            render_bullets(result["strengths"])
    with col_d:
        with st.container(border=True):
            st.markdown("#### 🛠️ Improvement Suggestions")
            render_bullets(result["improvement_suggestions"])

    # --- Raw JSON (useful for demos / viva) ---
    with st.expander("🔍 View raw JSON response"):
        st.json(result)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Settings")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        help="Get a free key at https://aistudio.google.com/apikey. "
        "You can also set the GEMINI_API_KEY environment variable.",
    )
    st.caption(f"Model: `{MODEL_NAME}`")
    st.divider()
    st.markdown(
        "**How it works**\n"
        "1. Upload a PDF resume\n"
        "2. Paste the job description\n"
        "3. Click **Analyze**\n"
        "4. Review the AI-generated report"
    )

# --------------------------------------------------------------------------- #
# Main page
# --------------------------------------------------------------------------- #
st.title("📄 Smart Resume Analyzer")
st.caption("AI-powered resume-to-job-description matching using Gemini 2.5 Flash")

left, right = st.columns(2, gap="large")

with left:
    st.subheader("1️⃣ Upload Resume")
    uploaded_pdf = st.file_uploader("Candidate resume (PDF only)", type=["pdf"])

with right:
    st.subheader("2️⃣ Job Description")
    job_description = st.text_area(
        "Paste the target job description",
        height=220,
        placeholder="Paste the full job description here...",
    )

analyze_clicked = st.button("🚀 Analyze", type="primary", use_container_width=True)

if analyze_clicked:
    api_key = get_api_key(api_key_input)

    # --- Input validation ---
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar.")
    elif uploaded_pdf is None:
        st.error("Please upload a resume in PDF format.")
    elif not job_description.strip():
        st.error("Please paste a job description.")
    else:
        try:
            with st.spinner("Reading resume..."):
                resume_text = extract_text_from_pdf(uploaded_pdf)

            if not resume_text:
                st.error(
                    "No text could be extracted. The PDF may be a scanned image; "
                    "please upload a text-based PDF."
                )
            else:
                with st.expander("📃 Extracted resume text (preview)"):
                    st.text(resume_text[:3000] + ("..." if len(resume_text) > 3000 else ""))

                with st.spinner("Analyzing with Gemini..."):
                    result = analyze_resume(api_key, resume_text, job_description)

                render_results(result)

        except json.JSONDecodeError:
            st.error("The model returned an invalid response. Please try again.")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:  # API errors, network issues, bad key, etc.
            st.error(f"Something went wrong: {e}")