"""
app.py
------
Medical Report Analyzer — AI-powered medical document analysis
Built with Streamlit + Ollama (Llama 3.2) + PyMuPDF

Run:
    ollama serve          (in one terminal)
    streamlit run app.py  (in another terminal)
"""

import json
import re
import time

import fitz  # PyMuPDF
import requests
import streamlit as st

# ── Configuration ──────────────────────────────────────────────────────────────
OLLAMA_BASE  = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"
APP_TITLE     = "Medical Report Analyzer"

# ── Page Setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp { background: #060d1a; }

/* ── Top header ── */
.app-header {
    background: linear-gradient(135deg, #0a4f3c 0%, #0d7a5c 50%, #0a4f3c 100%);
    border-radius: 16px;
    padding: 32px 36px 26px;
    margin-bottom: 28px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(13, 122, 92, 0.3);
    border: 1px solid #0d7a5c40;
}
.app-header h1 {
    color: #ffffff;
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 6px;
    letter-spacing: -0.5px;
}
.app-header p {
    color: #6ee7c7;
    font-size: 0.9rem;
    margin: 0;
}

/* ── Section cards ── */
.section-card {
    background: #0d1b2a;
    border: 1px solid #1a3a5c;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.section-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #0d7a5c;
    margin-bottom: 10px;
}

/* ── Metric cards ── */
.metrics-row {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.metric-card {
    background: #0d1b2a;
    border: 1px solid #1a3a5c;
    border-radius: 10px;
    padding: 16px 20px;
    flex: 1;
    min-width: 140px;
    text-align: center;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #0d7a5c;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Score ring ── */
.score-display {
    text-align: center;
    padding: 20px;
}
.score-number {
    font-size: 3.5rem;
    font-weight: 700;
    line-height: 1;
}
.score-label {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Tag badges ── */
.tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.tag {
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.78rem;
    font-weight: 500;
}
.tag-green  { background: #052e1a; border: 1px solid #065f46; color: #6ee7b7; }
.tag-red    { background: #2d0a0a; border: 1px solid #7f1d1d; color: #fca5a5; }
.tag-yellow { background: #2d2000; border: 1px solid #78350f; color: #fde68a; }
.tag-blue   { background: #0a1628; border: 1px solid #1e3a5f; color: #93c5fd; }

/* ── Chat bubbles ── */
.chat-user {
    background: #1e3a5f;
    border-radius: 14px 14px 3px 14px;
    padding: 12px 18px;
    margin: 10px 0 10px 80px;
    color: #dbeafe;
    font-size: 0.9rem;
    line-height: 1.6;
}
.chat-bot {
    background: #0d1b2a;
    border-left: 3px solid #0d7a5c;
    border-radius: 3px 14px 14px 14px;
    padding: 14px 18px;
    margin: 10px 80px 10px 0;
    color: #e2e8f0;
    font-size: 0.9rem;
    line-height: 1.7;
}
.chat-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.chat-user .chat-label { color: #60a5fa; }
.chat-bot  .chat-label { color: #0d7a5c; }

/* ── Warning / info boxes ── */
.warn-box {
    background: #2d1a00;
    border: 1px solid #92400e;
    border-radius: 10px;
    padding: 14px 18px;
    color: #fde68a;
    font-size: 0.88rem;
    margin-bottom: 16px;
}
.info-box {
    background: #0a1628;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 14px 18px;
    color: #93c5fd;
    font-size: 0.88rem;
    margin-bottom: 16px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #080f1a !important;
    border-right: 1px solid #1a2d40 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0a4f3c, #0d7a5c) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0d7a5c, #10b981) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(13,122,92,0.4) !important;
}

hr { border-color: #1a2d40 !important; }
</style>
""", unsafe_allow_html=True)


# ── Ollama Helpers ─────────────────────────────────────────────────────────────

def get_available_models() -> list[str]:
    """Fetch models installed in Ollama."""
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        data = r.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def ollama_chat(prompt: str, model: str, stream: bool = True):
    """
    Stream a response from Ollama.
    Yields text chunks when stream=True, returns full string when stream=False.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }
    try:
        with requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            stream=stream,
            timeout=120,
        ) as resp:
            resp.raise_for_status()
            if stream:
                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield chunk.get("response", "")
                        if chunk.get("done"):
                            break
            else:
                full = ""
                for line in resp.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        full += chunk.get("response", "")
                        if chunk.get("done"):
                            break
                return full
    except requests.exceptions.ConnectionError:
        yield "⚠️ Cannot connect to Ollama. Make sure `ollama serve` is running."
    except Exception as e:
        yield f"⚠️ Error: {e}"


# ── Document Processing ────────────────────────────────────────────────────────

def extract_text_from_pdf(file) -> str:
    """Extract all text from an uploaded PDF using PyMuPDF."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_text_from_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore").strip()


def extract_document_text(uploaded_file) -> str:
    """Route file to correct extractor based on type."""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif name.endswith(".txt"):
        return extract_text_from_txt(uploaded_file)
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore").strip()


# ── Prompts ────────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are an expert medical report analyst. Analyze the following medical report carefully and provide a comprehensive, structured analysis.

MEDICAL REPORT:
{report_text}

Provide your analysis in the following exact format:

PATIENT_SUMMARY:
[2-3 sentences summarizing who the patient is and what type of report this is]

KEY_FINDINGS:
[List the most important medical findings, one per line starting with •]

ABNORMAL_VALUES:
[List any values outside normal range, one per line starting with ⚠]
[If all values are normal, write: All values within normal range]

NORMAL_VALUES:
[List key values that are within normal range, one per line starting with ✓]

DIAGNOSES_CONDITIONS:
[List identified diagnoses or conditions, one per line starting with •]
[If none explicitly stated, write: No explicit diagnosis stated]

MEDICATIONS_MENTIONED:
[List any medications, one per line starting with •]
[If none, write: None mentioned]

RECOMMENDATIONS:
[List medical recommendations or next steps, one per line starting with •]

HEALTH_SCORE:
[A number from 1-10 based on overall report findings, where 10 is excellent health]

SEVERITY_LEVEL:
[One of: NORMAL / MILD CONCERN / MODERATE CONCERN / SERIOUS / CRITICAL]

PLAIN_ENGLISH_SUMMARY:
[Explain the entire report in simple language a patient with no medical background can understand. 3-5 sentences.]

IMPORTANT_DISCLAIMER:
This analysis is AI-generated for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional for diagnosis and treatment."""


QA_PROMPT = """You are a helpful medical report assistant. You have access to the following medical report:

MEDICAL REPORT:
{report_text}

A patient is asking you a question about their report. Answer clearly, accurately, and in simple language. If the answer is not in the report, say so honestly. Always remind them to consult their doctor for medical decisions.

Question: {question}

Answer:"""


# ── Analysis Parser ────────────────────────────────────────────────────────────

def parse_analysis(text: str) -> dict:
    """Parse structured AI response into a dictionary."""
    sections = {
        "patient_summary": "",
        "key_findings": [],
        "abnormal_values": [],
        "normal_values": [],
        "diagnoses": [],
        "medications": [],
        "recommendations": [],
        "health_score": "N/A",
        "severity": "UNKNOWN",
        "plain_english": "",
    }

    def extract(label: str) -> str:
        pattern = rf"{label}:\s*(.*?)(?=\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def to_list(raw: str) -> list[str]:
        lines = [l.strip().lstrip("•⚠✓-").strip() for l in raw.split("\n") if l.strip()]
        return [l for l in lines if l and len(l) > 2]

    sections["patient_summary"] = extract("PATIENT_SUMMARY")
    sections["key_findings"]    = to_list(extract("KEY_FINDINGS"))
    sections["abnormal_values"] = to_list(extract("ABNORMAL_VALUES"))
    sections["normal_values"]   = to_list(extract("NORMAL_VALUES"))
    sections["diagnoses"]       = to_list(extract("DIAGNOSES_CONDITIONS"))
    sections["medications"]     = to_list(extract("MEDICATIONS_MENTIONED"))
    sections["recommendations"] = to_list(extract("RECOMMENDATIONS"))
    sections["plain_english"]   = extract("PLAIN_ENGLISH_SUMMARY")

    # Health score
    score_raw = extract("HEALTH_SCORE")
    score_match = re.search(r"\d+", score_raw)
    sections["health_score"] = score_match.group() if score_match else "N/A"

    # Severity
    severity_raw = extract("SEVERITY_LEVEL").upper()
    for level in ["CRITICAL", "SERIOUS", "MODERATE CONCERN", "MILD CONCERN", "NORMAL"]:
        if level in severity_raw:
            sections["severity"] = level
            break

    return sections


def severity_color(level: str) -> str:
    colors = {
        "NORMAL": "#10b981",
        "MILD CONCERN": "#f59e0b",
        "MODERATE CONCERN": "#f97316",
        "SERIOUS": "#ef4444",
        "CRITICAL": "#dc2626",
    }
    return colors.get(level, "#64748b")


def score_color(score: str) -> str:
    try:
        s = int(score)
        if s >= 8: return "#10b981"
        if s >= 6: return "#f59e0b"
        if s >= 4: return "#f97316"
        return "#ef4444"
    except Exception:
        return "#64748b"


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Medical Analyzer")
    st.markdown("---")

    # Model selector
    st.markdown("### 🤖 AI Model")
    available = get_available_models()
    if available:
        model = st.selectbox("Select Model", available, index=0)
    else:
        st.error("Ollama not running. Start with:\n```\nollama serve\n```")
        model = DEFAULT_MODEL

    st.markdown("---")
    st.markdown("### 📄 Supported Formats")
    st.markdown("""
- 📕 PDF medical reports
- 📝 TXT plain text reports
- 🩺 Blood test results
- 🫁 Radiology reports
- 💊 Prescription summaries
- 🧪 Lab reports
    """)

    st.markdown("---")
    st.markdown("### 🔒 Privacy")
    st.markdown("""
**100% Local Processing**

Your medical data never leaves your machine. No cloud APIs, no external servers, no data logging.
    """)

    st.markdown("---")
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("""
This tool is for **informational purposes only**. Always consult a qualified healthcare professional for medical decisions.
    """)

    if st.button("🗑️ Clear Session"):
        for key in ["analysis", "parsed", "doc_text", "chat_history"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🏥 Medical Report Analyzer</h1>
    <p>AI-powered medical document analysis · 100% local · Powered by Ollama + Llama 3.2</p>
</div>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analysis"     not in st.session_state:
    st.session_state.analysis = None
if "parsed"       not in st.session_state:
    st.session_state.parsed = None
if "doc_text"     not in st.session_state:
    st.session_state.doc_text = None

# ── Upload Section ─────────────────────────────────────────────────────────────
st.markdown("### 📤 Upload Medical Report")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader(
        "Upload your medical report",
        type=["pdf", "txt"],
        help="Supported: PDF, TXT",
        label_visibility="collapsed",
    )
with col2:
    patient_name = st.text_input("Patient Name (optional)", placeholder="e.g. Ahmed Khan")

if uploaded:
    with st.spinner("Reading document..."):
        doc_text = extract_document_text(uploaded)
        st.session_state.doc_text = doc_text

    word_count = len(doc_text.split())
    char_count = len(doc_text)

    st.markdown(f"""
    <div class="info-box">
        ✅ <strong>{uploaded.name}</strong> loaded successfully —
        {word_count:,} words · {char_count:,} characters
    </div>
    """, unsafe_allow_html=True)

    # Analyze button
    if st.button("🔍 Analyze Medical Report", use_container_width=True):
        st.session_state.analysis = None
        st.session_state.parsed   = None
        st.session_state.chat_history = []

        prompt = ANALYSIS_PROMPT.format(report_text=doc_text[:4000])

        with st.spinner("AI is analyzing your report... This may take 30–60 seconds."):
            full_response = ""
            for chunk in ollama_chat(prompt, model, stream=True):
                full_response += chunk

        st.session_state.analysis = full_response
        st.session_state.parsed   = parse_analysis(full_response)
        st.rerun()

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.parsed:
    p = st.session_state.parsed
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    # ── Top metrics row ──
    score     = p["health_score"]
    severity  = p["severity"]
    s_color   = score_color(score)
    sev_color = severity_color(severity)
    abnormal_count = len([v for v in p["abnormal_values"] if "normal range" not in v.lower()])
    findings_count = len(p["key_findings"])

    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-card">
            <div class="metric-value" style="color:{s_color}">{score}<span style="font-size:1rem">/10</span></div>
            <div class="metric-label">Health Score</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color:{sev_color}; font-size:1.1rem; padding-top:8px">{severity}</div>
            <div class="metric-label">Severity Level</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color:#ef4444">{abnormal_count}</div>
            <div class="metric-label">Abnormal Values</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color:#60a5fa">{findings_count}</div>
            <div class="metric-label">Key Findings</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two column layout ──
    left, right = st.columns(2)

    with left:
        # Patient Summary
        if p["patient_summary"]:
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">👤 Patient Summary</div>
                <p style="color:#cbd5e1; font-size:0.9rem; line-height:1.7; margin:0">{p["patient_summary"]}</p>
            </div>
            """, unsafe_allow_html=True)

        # Key Findings
        if p["key_findings"]:
            findings_html = "".join(
                f'<span class="tag tag-blue">{f}</span>' for f in p["key_findings"]
            )
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">🔍 Key Findings</div>
                <div class="tag-row">{findings_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # Diagnoses
        if p["diagnoses"]:
            diag_html = "".join(
                f'<span class="tag tag-yellow">{d}</span>' for d in p["diagnoses"]
            )
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">🩺 Diagnoses / Conditions</div>
                <div class="tag-row">{diag_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # Medications
        if p["medications"]:
            med_html = "".join(
                f'<span class="tag tag-blue">{m}</span>' for m in p["medications"]
            )
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">💊 Medications</div>
                <div class="tag-row">{med_html}</div>
            </div>
            """, unsafe_allow_html=True)

    with right:
        # Abnormal Values
        if p["abnormal_values"]:
            abn_html = "".join(
                f'<span class="tag tag-red">⚠ {v}</span>' for v in p["abnormal_values"]
            )
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">⚠️ Abnormal Values</div>
                <div class="tag-row">{abn_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # Normal Values
        if p["normal_values"]:
            norm_html = "".join(
                f'<span class="tag tag-green">✓ {v}</span>' for v in p["normal_values"]
            )
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">✅ Normal Values</div>
                <div class="tag-row">{norm_html}</div>
            </div>
            """, unsafe_allow_html=True)

        # Recommendations
        if p["recommendations"]:
            rec_items = "".join(
                f'<li style="color:#cbd5e1; margin-bottom:6px">{r}</li>'
                for r in p["recommendations"]
            )
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">📋 Recommendations</div>
                <ul style="margin:0; padding-left:18px">{rec_items}</ul>
            </div>
            """, unsafe_allow_html=True)

    # ── Plain English Summary ──
    if p["plain_english"]:
        st.markdown(f"""
        <div class="section-card" style="border-color:#0d7a5c; background:#071a12">
            <div class="section-title">💬 What This Means For You</div>
            <p style="color:#a7f3d0; font-size:0.95rem; line-height:1.8; margin:0">{p["plain_english"]}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Disclaimer ──
    st.markdown("""
    <div class="warn-box">
        ⚠️ <strong>Medical Disclaimer:</strong> This AI analysis is for informational purposes only and does not constitute medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional.
    </div>
    """, unsafe_allow_html=True)

    # ── Q&A Chat ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 💬 Ask About Your Report")
    st.markdown("""
    <div class="info-box">
        Ask any question about your medical report and the AI will answer based on your document.
    </div>
    """, unsafe_allow_html=True)

    # Suggested questions
    st.markdown("**Quick questions:**")
    suggestions = [
        "Should I be worried about my results?",
        "What do the abnormal values mean?",
        "What should I do next?",
        "Explain my diagnosis in simple terms",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"q{i}"):
            st.session_state["_pending_q"] = s
            st.rerun()

    # Chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user"><div class="chat-label">You</div>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-bot"><div class="chat-label">🏥 Medical AI</div>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    # Chat input
    question = st.chat_input("Ask a question about your report...")

    if "_pending_q" in st.session_state:
        question = st.session_state.pop("_pending_q")

    if question and st.session_state.doc_text:
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.markdown(
            f'<div class="chat-user"><div class="chat-label">You</div>{question}</div>',
            unsafe_allow_html=True,
        )

        prompt = QA_PROMPT.format(
            report_text=st.session_state.doc_text[:4000],
            question=question,
        )
        with st.spinner("Thinking..."):
            answer = ""
            for chunk in ollama_chat(prompt, model, stream=True):
                answer += chunk

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.markdown(
            f'<div class="chat-bot"><div class="chat-label">🏥 Medical AI</div>{answer}</div>',
            unsafe_allow_html=True,
        )
        st.rerun()

elif not uploaded:
    # Landing state
    st.markdown("""
    <div class="section-card" style="text-align:center; padding: 40px;">
        <div style="font-size: 3rem; margin-bottom: 16px">🏥</div>
        <div style="color: #94a3b8; font-size: 0.95rem; line-height: 1.8">
            Upload a medical report above to get started.<br>
            Supports blood tests, radiology reports, prescriptions, lab results, and more.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    st.markdown("### ✨ What This Tool Does")
    f1, f2, f3 = st.columns(3)
    features = [
        ("🔍", "Smart Analysis", "Extracts key findings, abnormal values, diagnoses, and medications automatically"),
        ("💬", "Plain English", "Explains complex medical terminology in simple language anyone can understand"),
        ("🤖", "Interactive Q&A", "Ask follow-up questions about your report and get instant AI-powered answers"),
    ]
    for col, (icon, title, desc) in zip([f1, f2, f3], features):
        col.markdown(f"""
        <div class="section-card" style="text-align:center">
            <div style="font-size:2rem; margin-bottom:10px">{icon}</div>
            <div style="color:#e2e8f0; font-weight:600; margin-bottom:8px">{title}</div>
            <div style="color:#64748b; font-size:0.83rem; line-height:1.6">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
