# ═══════════════════════════════════════════════════════════════════════════
#  MedScan AI  —  Universal Medical Report Analyzer
#  Stack : Streamlit + Groq (Llama) + PyMuPDF + Plotly
# ═══════════════════════════════════════════════════════════════════════════

import os, io, re, json, logging, tempfile
from datetime import datetime
from typing import Dict, List, Optional

# ── .env loader (optional — app works without it if key is set in env) ────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # No .env file support, but os.environ still works

# ── Reference database ────────────────────────────────────────────────────────
try:
    from reference_data import (
        get_reference, check_status as db_check_status,
        find_test, total_tests, total_aliases, REFERENCE_DB
    )
    DB_OK = True
except ImportError:
    DB_OK = False
    # Stub functions so app never crashes
    def get_reference(*a, **kw): return None
    def db_check_status(*a, **kw): return "unknown"
    def find_test(*a, **kw): return None
    def total_tests(): return 0
    def total_aliases(): return 0
    REFERENCE_DB = {}

# ── Streamlit (REQUIRED — cannot run without it) ──────────────────────────────
try:
    import streamlit as st
except ImportError:
    raise SystemExit(
        "CRITICAL: Streamlit is not installed.\n"
        "Run: pip install streamlit"
    )

# ── Pandas (REQUIRED for CSV export) ─────────────────────────────────────────
try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False
    pd = None

# ── Plotly (optional — charts won't show without it) ─────────────────────────
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False
    go = None

# ── Groq (REQUIRED for AI analysis) ─────────────────────────────────────────
try:
    from openai import OpenAI as GroqClient
    GROQ_OK = True
except ImportError:
    GROQ_OK = False
    GroqClient = None

# ── PIL / Pillow (needed for image reports) ───────────────────────────────────
try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False
    Image = None

# ── PDF extraction (PyMuPDF) ──────────────────────────────────────────────────
try:
    import fitz  # PyMuPDF
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

# ── OCR fallback (Tesseract) ──────────────────────────────────────────────────
try:
    import pytesseract
    OCR_OK = True
except ImportError:
    OCR_OK = False

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("medscan")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — STYLES
# ═══════════════════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:        #080c12;
  --surface:   #0e1520;
  --surface2:  #141e2e;
  --surface3:  #1a2540;
  --border:    rgba(99,178,255,0.08);
  --border2:   rgba(99,178,255,0.16);
  --text:      #dce8f8;
  --muted:     #5a7090;
  --subtle:    #8fa8c8;
  --blue:      #3b9eff;
  --blue-soft: rgba(59,158,255,0.12);
  --blue-glow: rgba(59,158,255,0.22);
  --green:     #2dd4a0;
  --green-soft:rgba(45,212,160,0.10);
  --red:       #ff5c6a;
  --red-soft:  rgba(255,92,106,0.10);
  --amber:     #ffb547;
  --amber-soft:rgba(255,181,71,0.10);
  --purple:    #a78bfa;
  --r-sm: 6px; --r-md: 10px; --r-lg: 16px; --r-xl: 22px;
}

*,*::before,*::after{box-sizing:border-box}
html,body,.stApp{
  font-family:'Syne',sans-serif!important;
  background:var(--bg)!important;
  color:var(--text)!important;
}
.main .block-container{padding:2rem 2.5rem 5rem!important;max-width:1320px!important}

/* scrollbar */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--surface)}
::-webkit-scrollbar-thumb{background:var(--surface3);border-radius:99px}

/* hide streamlit chrome */
#MainMenu,footer,header{visibility:hidden}

/* ── HEADER ── */
.app-header{
  display:flex;align-items:center;gap:16px;
  padding:0 0 24px;margin-bottom:8px;
  border-bottom:1px solid var(--border);
}
.app-logo{
  width:52px;height:52px;border-radius:var(--r-md);
  background:var(--blue-soft);border:1px solid var(--blue-glow);
  display:flex;align-items:center;justify-content:center;font-size:24px;
  flex-shrink:0;
}
.app-title{font-size:1.55rem;font-weight:800;color:var(--text);letter-spacing:-0.03em;margin:0}
.app-sub{font-size:0.8rem;color:var(--muted);margin:2px 0 0;font-weight:400}

/* ── DISCLAIMER ── */
.disclaimer{
  display:flex;align-items:center;gap:10px;
  padding:10px 16px;margin-bottom:20px;
  background:rgba(255,181,71,0.06);
  border:1px solid rgba(255,181,71,0.18);
  border-radius:var(--r-md);
  font-size:0.8rem;color:var(--amber);
}

/* ── CARDS ── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r-lg);padding:20px 24px;margin-bottom:12px;
  transition:border-color .2s;
}
.card:hover{border-color:var(--border2)}

/* ── STAT CHIPS ── */
.stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.stat{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r-md);padding:14px 16px;position:relative;
  overflow:hidden;transition:transform .2s,border-color .2s;
}
.stat:hover{transform:translateY(-2px);border-color:var(--border2)}
.stat::after{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:var(--stat-color,var(--blue));
}
.stat-label{font-size:.68rem;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.stat-value{font-size:1.8rem;font-weight:800;color:var(--text);
  letter-spacing:-.04em;line-height:1}
.stat-icon{position:absolute;top:12px;right:14px;font-size:1.1rem;opacity:.3}

/* ── SECTION TITLES ── */
.sec{
  display:flex;align-items:center;gap:8px;
  padding-bottom:8px;margin-bottom:14px;
  border-bottom:1px solid var(--border);
}
.sec-dot{width:6px;height:6px;border-radius:50%;background:var(--blue);flex-shrink:0}
.sec h3{font-size:.85rem!important;font-weight:700!important;
  color:var(--text)!important;margin:0!important;letter-spacing:.02em;
  text-transform:uppercase}

/* ── STATUS BADGES ── */
.badge{
  display:inline-flex;align-items:center;gap:4px;
  padding:3px 10px;border-radius:99px;
  font-size:.72rem;font-weight:700;letter-spacing:.03em;
  white-space:nowrap;
}
.b-normal {background:var(--green-soft);color:var(--green);border:1px solid rgba(45,212,160,.2)}
.b-high   {background:var(--red-soft);  color:var(--red);  border:1px solid rgba(255,92,106,.2)}
.b-low    {background:var(--amber-soft);color:var(--amber);border:1px solid rgba(255,181,71,.2)}
.b-abnormal{background:var(--red-soft); color:var(--red);  border:1px solid rgba(255,92,106,.2)}
.b-borderline{background:var(--amber-soft);color:var(--amber);border:1px solid rgba(255,181,71,.2)}
.b-info   {background:rgba(99,178,255,.08);color:var(--subtle);border:1px solid var(--border2)}

/* ── TABLE ── */
.report-table{width:100%;border-collapse:collapse;background:var(--surface)}
.report-table thead tr{background:var(--surface2)}
.report-table thead th{
  padding:10px 14px;text-align:left;
  font-size:.65rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);
  border-bottom:1px solid var(--border2);
}
.report-table tbody tr{border-top:1px solid var(--border);transition:background .15s}
.report-table tbody tr:hover{background:var(--surface2)}
.report-table tbody tr.row-high{background:rgba(255,92,106,.04)}
.report-table tbody tr.row-low {background:rgba(255,181,71,.04)}
.report-table tbody tr.row-abnormal{background:rgba(255,92,106,.04)}
.report-table tbody tr.row-borderline{background:rgba(255,181,71,.04)}
.report-table td{padding:11px 14px;font-size:.84rem;vertical-align:middle}
.td-name{color:var(--text);font-weight:600}
.td-val {font-family:'JetBrains Mono',monospace;font-size:.85rem;font-weight:500}
.td-val.v-high{color:var(--red)}
.td-val.v-low {color:var(--amber)}
.td-val.v-normal{color:var(--text)}
.td-ref{color:var(--subtle);font-size:.8rem}
.td-note{font-size:.72rem;color:var(--purple);margin-top:2px}

/* ── PATIENT INFO ── */
.pt-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:18px}
.pt-field{background:var(--surface2);border:1px solid var(--border);
  border-radius:var(--r-md);padding:10px 14px}
.pt-label{font-size:.63rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.pt-value{font-size:.9rem;font-weight:600;color:var(--text)}

/* ── RISK CARDS ── */
.risk-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px}
.risk-card{
  border-radius:var(--r-md);padding:16px;text-align:center;position:relative;overflow:hidden;
  border:1px solid var(--border);
}
.risk-label{font-size:.63rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin-bottom:8px;position:relative;z-index:1}
.risk-val{font-size:1.1rem;font-weight:800;position:relative;z-index:1;letter-spacing:-.02em}
.risk-low   {background:var(--green-soft)}.risk-low   .risk-val{color:var(--green)}
.risk-mod   {background:var(--amber-soft)}.risk-mod   .risk-val{color:var(--amber)}
.risk-high  {background:var(--red-soft)}  .risk-high  .risk-val{color:var(--red)}

/* ── RECOMMENDATION ITEMS ── */
.rec{
  display:flex;gap:12px;padding:12px 14px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r-md);margin-bottom:6px;transition:border-color .15s;
}
.rec:hover{border-color:var(--border2)}
.rec-dot{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0}
.rec-dot.p-high  {background:var(--red);  box-shadow:0 0 6px var(--red)}
.rec-dot.p-medium{background:var(--amber);box-shadow:0 0 6px var(--amber)}
.rec-dot.p-low   {background:var(--blue); box-shadow:0 0 6px var(--blue)}
.rec-body{}
.rec-text{font-size:.86rem;color:var(--text);line-height:1.55;font-weight:500}
.rec-why {font-size:.76rem;color:var(--muted);margin-top:3px;line-height:1.4}

/* ── REPORT TYPE PILL ── */
.rtype{
  display:inline-flex;align-items:center;gap:6px;
  padding:5px 14px;border-radius:99px;
  background:rgba(167,139,250,.1);color:var(--purple);
  border:1px solid rgba(167,139,250,.25);
  font-size:.78rem;font-weight:700;letter-spacing:.03em;
  margin-bottom:16px;
}

/* ── FINDING ROWS ── */
.finding{
  display:flex;gap:10px;align-items:flex-start;
  padding:10px 14px;border-radius:var(--r-md);margin-bottom:5px;
}
.finding-high{background:var(--red-soft);border:1px solid rgba(255,92,106,.18)}
.finding-low {background:var(--amber-soft);border:1px solid rgba(255,181,71,.18)}
.finding-icon{font-size:.9rem;margin-top:1px;flex-shrink:0}
.finding-text{font-size:.84rem;color:var(--text);line-height:1.5}

/* ── CRITICAL ALERT ── */
.critical{
  display:flex;gap:10px;align-items:flex-start;
  padding:12px 16px;border-radius:var(--r-md);margin-bottom:6px;
  background:rgba(255,92,106,.1);border:2px solid rgba(255,92,106,.35);
}
.critical-text{font-size:.88rem;color:var(--red);font-weight:600}

/* ── SUMMARY BOX ── */
.summary-box{
  background:var(--surface2);border:1px solid var(--border2);
  border-radius:var(--r-md);padding:18px 20px;
}
.summary-label{font-size:.63rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--blue);margin-bottom:8px}
.summary-text{font-size:.88rem;color:var(--subtle);line-height:1.7}

/* ── FOLLOW UP ── */
.followup{
  display:flex;gap:10px;align-items:flex-start;
  padding:9px 14px;border-radius:var(--r-md);margin-bottom:5px;
  background:rgba(255,181,71,.05);border:1px solid rgba(255,181,71,.15);
}
.followup-text{font-size:.84rem;color:var(--text)}

/* ── POSITIVE ── */
.positive{
  display:flex;gap:8px;padding:8px 12px;border-radius:var(--r-md);margin-bottom:4px;
  background:var(--green-soft);border:1px solid rgba(45,212,160,.15);
}
.positive-text{font-size:.82rem;color:var(--subtle)}

/* ── EXPORT CARDS ── */
.exp-card{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:var(--r-md);padding:16px;text-align:center;margin-bottom:8px;
}
.exp-icon{font-size:1.6rem;margin-bottom:6px}
.exp-title{font-size:.85rem;font-weight:700;color:var(--text);margin-bottom:2px}
.exp-sub{font-size:.73rem;color:var(--muted)}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{
  background:var(--surface)!important;border-radius:var(--r-lg)!important;
  padding:4px!important;gap:2px!important;
  border:1px solid var(--border)!important;margin-bottom:20px!important;
}
.stTabs [data-baseweb="tab"]{
  background:transparent!important;border-radius:var(--r-md)!important;
  color:var(--muted)!important;font-size:.82rem!important;font-weight:600!important;
  padding:8px 18px!important;transition:all .15s!important;border:none!important;
  font-family:'Syne',sans-serif!important;letter-spacing:.02em!important;
}
.stTabs [data-baseweb="tab"]:hover{
  background:var(--surface3)!important;color:var(--text)!important;
}
.stTabs [aria-selected="true"]{
  background:var(--surface3)!important;color:var(--text)!important;
}
.stTabs [data-baseweb="tab-border"]{display:none!important}
.stTabs [data-baseweb="tab-highlight"]{display:none!important}

/* ── BUTTONS ── */
.stButton>button{
  font-family:'Syne',sans-serif!important;font-weight:700!important;
  border-radius:var(--r-md)!important;transition:all .15s!important;
  letter-spacing:.02em!important;
}
.stButton>button[kind="primary"]{
  background:var(--blue)!important;color:#fff!important;
  border:none!important;
}
.stButton>button[kind="primary"]:hover{
  background:#2d8ef0!important;transform:translateY(-1px);
  box-shadow:0 4px 20px var(--blue-glow)!important;
}
.stButton>button[kind="secondary"]{
  background:var(--surface2)!important;color:var(--text)!important;
  border:1px solid var(--border2)!important;
}
.stDownloadButton>button{
  font-family:'Syne',sans-serif!important;font-weight:700!important;
  background:var(--surface2)!important;color:var(--text)!important;
  border:1px solid var(--border2)!important;border-radius:var(--r-md)!important;
  width:100%!important;transition:all .15s!important;
}
.stDownloadButton>button:hover{
  border-color:var(--blue)!important;color:var(--blue)!important;
  background:var(--blue-soft)!important;
}

/* ── FILE UPLOADER ── */
.stFileUploader{
  background:var(--surface)!important;border:1.5px dashed var(--border2)!important;
  border-radius:var(--r-xl)!important;padding:24px!important;transition:all .2s!important;
}
.stFileUploader:hover{border-color:var(--blue)!important;background:var(--blue-soft)!important}
.stFileUploader [data-testid="stFileUploaderDropzone"]{background:transparent!important;border:none!important}

/* ── EXPANDER ── */
.streamlit-expanderHeader{
  background:var(--surface)!important;border:1px solid var(--border)!important;
  border-radius:var(--r-md)!important;color:var(--text)!important;
  font-family:'Syne',sans-serif!important;font-weight:600!important;
  font-size:.85rem!important;padding:12px 16px!important;
}
.streamlit-expanderHeader:hover{
  border-color:var(--border2)!important;background:var(--surface2)!important;
}
.streamlit-expanderContent{
  background:var(--surface)!important;border:1px solid var(--border)!important;
  border-top:none!important;border-radius:0 0 var(--r-md) var(--r-md)!important;
  padding:14px!important;
}

/* ── ALERTS ── */
.stAlert{background:var(--surface2)!important;border-radius:var(--r-md)!important;
  border:1px solid var(--border)!important;font-family:'Syne',sans-serif!important}
.stSpinner>div{border-top-color:var(--blue)!important}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"]{
  background:var(--surface)!important;border-right:1px solid var(--border)!important;
}
section[data-testid="stSidebar"] .block-container{padding:20px 16px!important}
.stCheckbox label{
  font-family:'Syne',sans-serif!important;font-size:.82rem!important;
  color:var(--subtle)!important;
}

/* ── PLOTLY ── */
.js-plotly-plot .plotly,.plot-container{background:transparent!important}

hr{border:none;border-top:1px solid var(--border)!important;margin:20px 0!important}
</style>
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — GEMINI PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

PARSE_PROMPT = """
You are a precise medical data extraction engine. Analyze the lab report text below and return structured JSON.

REPORT TEXT:
{text}

━━━ EXTRACTION RULES ━━━

RULE 1 — PATIENT INFO ONLY in patient_info:
Extract name, age, gender, report_date, lab_number, referring_doctor, lab_name.
These fields MUST ONLY contain patient/admin data — never test results.

RULE 2 — NEVER put these in test_categories (they are metadata, not tests):
• Lab.Reg.No, UHID, Registration Number, Sample ID, Barcode, Accession No
• Age, Date of Birth, Sex, Gender, Blood Group, Weight, Height
• Collection Date, Received Date, Report Date, Reported By
• Referred By, Doctor Name, Hospital Name, Lab Address
• Page numbers, disclaimers, signatures, any header/footer text
If a line contains "Lab.Reg.No 4701 AGE 21 SEX Male" → ALL goes to patient_info, NONE to tests.

RULE 3 — TEST STATUS (compare value vs reference range in the report):
• "normal"     = value is within reference range
• "high"       = value is ABOVE upper limit  
• "low"        = value is BELOW lower limit
• "abnormal"   = qualitative result that is clinically abnormal (Positive, Present, Detected)
• "borderline" = value is at the very edge of normal range
• "info"       = observation only — colour, appearance, microscopy description

RULE 4 — HANDLE ALL REPORT TYPES:
Blood (CBC, LFT, KFT, TFT, Lipid, HbA1c, Iron, Vitamins, Hormones, Cardiac, Tumour markers)
Urine Routine (physical, chemical, microscopy — ALL rows are tests, not metadata)
Stool Analysis, Culture & Sensitivity, Coagulation, Autoimmune, Allergy panels

RULE 5 — For qualitative tests (urine colour, culture results, microscopy):
value = actual finding (e.g. "Yellow", "E. coli", "2-4 /hpf")
reference_range = expected normal (e.g. "Yellow", "No growth", "0-2 /hpf")
status = "info" for colour/appearance, "normal"/"abnormal" for findings

RULE 6 — NEVER invent values. Only extract what is explicitly in the report.

Return ONLY this JSON (no extra text, no markdown):
{{
  "report_type": "Specific report name e.g. Complete Blood Count, Urine Routine, Lipid Panel",
  "patient_info": {{
    "name": "patient name only",
    "age": "e.g. 21 Years or Not specified",
    "gender": "Male/Female or Not specified",
    "report_date": "date or Not specified",
    "lab_number": "lab/UHID number or Not specified",
    "referring_doctor": "doctor name or Not specified",
    "lab_name": "lab name or Not specified"
  }},
  "test_categories": [
    {{
      "category": "section name e.g. Complete Blood Count",
      "tests": [
        {{
          "name": "exact test name",
          "value": "exact result value",
          "unit": "unit or empty string",
          "ref_range": "reference range as printed or Not specified",
          "status": "normal|high|low|abnormal|borderline|info",
          "flag": "H or L or empty — any flag letter printed in the report"
        }}
      ]
    }}
  ],
  "abnormal_findings": [
    "One plain-English sentence per abnormal result e.g. Haemoglobin 9.2 g/dL is Low (ref: 13.0–17.0)"
  ],
  "critical_values": [
    "Only truly critical/dangerous values needing immediate attention"
  ]
}}
"""

INSIGHTS_PROMPT = """
You are a senior clinical health educator. Analyze this patient's lab report and give PERSONALISED advice.

PATIENT: {patient}
REPORT TYPE: {report_type}

ALL TEST RESULTS:
{all_tests}

ABNORMAL RESULTS:
{abnormal_tests}

OVERALL RISK SCORE: {risk_score} ({risk_level})

Return ONLY this JSON (no extra text):
{{
  "conditions": [
    {{
      "name": "condition name",
      "probability": "low|moderate|high",
      "evidence": ["specific test + value supporting this"],
      "explanation": "2-sentence explanation using the patient's actual values"
    }}
  ],
  "recommendations": [
    {{
      "category": "dietary|lifestyle|medical|follow-up|urgent",
      "text": "Specific advice mentioning the actual test name and value",
      "priority": "low|medium|high",
      "reason": "Why this matters for this patient specifically"
    }}
  ],
  "follow_up_tests": [
    "Specific test + timing e.g. Repeat HbA1c in 3 months"
  ],
  "red_flags": [
    "Only if a value is critically dangerous — needs same-day medical attention"
  ],
  "summary": "3-4 sentence personalised summary. Mention patient name if known, key abnormal values, risk level, top action."
}}

RULES:
- Every recommendation MUST name the specific test and the patient's value
- If all results are normal give positive reinforcement + preventive tips for age/gender
- Tailor advice to the report type (urine culture ≠ lipid panel advice)
- Do NOT give generic advice that could apply to anyone
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns for rows that are metadata, NOT lab tests
_META = re.compile(
    r"""(?ix)^(
      lab[\s\.]*(reg|registration|no|number|id|code|ref|report)
      |uhid|patient[\s]*id|sample[\s]*id|barcode|accession
      |age|d[\s]*o[\s]*b|date[\s]*of[\s]*birth
      |sex|gender|blood[\s]*group
      |collection[\s]*date|received[\s]*date|report[\s]*date
      |reported[\s]*by|ref[\s]*by|referred[\s]*by
      |doctor|consultant|physician|clinician
      |weight|height|ward|bed[\s]*no
      |hospital|clinic|laboratory|lab[\s]*name|address|phone|tel
      |page[\s]*\d|printed|generated|disclaimer
    )""",
)


def _is_metadata(name: str, value: str) -> bool:
    """True if this row is patient/admin metadata, not a real test."""
    n, v = name.strip(), str(value).strip()
    if _META.match(n):
        return True
    # value is a date
    if re.match(r'^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$', v):
        return True
    # value is a year
    if re.match(r'^20\d{2}$', v):
        return True
    # value is "Years", "Male", "Female"
    if re.match(r'^(years?|male|female|m|f)$', v, re.I):
        return True
    # name has reg no / uhid fragments
    if re.search(r'(?i)(reg[\s\.]*no|lab[\s\.]*no|uhid)', n):
        return True
    return False


def extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF."""
    if not PYMUPDF_OK:
        return ""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc):
            txt = page.get_text("text")
            if txt.strip():
                pages.append(f"--- Page {i+1} ---\n{txt}")
        return "\n".join(pages)
    except Exception as e:
        log.error(f"PDF extract error: {e}")
        return ""


def extract_image(file_bytes: bytes, client) -> str:
    """Extract text from image using Groq Vision (Llama 4 Scout)."""
    if not PIL_OK:
        log.warning("Pillow not installed — cannot process image files")
        return ""
    try:
        import base64
        # Detect image format
        img = Image.open(io.BytesIO(file_bytes))
        fmt = (img.format or "JPEG").lower()
        mime = {"jpeg": "image/jpeg", "jpg": "image/jpeg",
                "png": "image/png", "bmp": "image/bmp",
                "tiff": "image/tiff", "webp": "image/webp"}.get(fmt, "image/jpeg")
        # Convert to JPEG if needed (smaller, faster)
        if fmt not in ("jpeg", "jpg", "png"):
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=85)
            file_bytes = buf.getvalue()
            mime = "image/jpeg"
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"}
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a medical lab report image. "
                            "Transcribe ALL text EXACTLY as printed — preserve every number, unit, "
                            "reference range, flag (H/L/*/\u2020), test name, and patient info line. "
                            "Maintain the column structure. Do not interpret, summarise, or skip anything."
                        )
                    }
                ]
            }],
            max_tokens=4000,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        log.error(f"Image extract error: {e}")
        return ""


def extract_image_ocr(file_bytes: bytes) -> str:
    """Fallback OCR using Tesseract."""
    if not OCR_OK or not PIL_OK:
        return ""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img)
    except Exception as e:
        log.error(f"OCR error: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — PARSING & STATUS LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def clean_json(text: str) -> str:
    """Strip markdown code fences and find the JSON object."""
    if "```json" in text:
        s = text.find("```json") + 7
        e = text.rfind("```")
        if e > s:
            text = text[s:e]
    elif "```" in text:
        s = text.find("```") + 3
        e = text.rfind("```")
        if e > s:
            text = text[s:e]
    text = text.strip()
    if not text.startswith("{"):
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group()
    return text


def fix_status(test: dict, gender: str = "male", age: int = 30) -> dict:
    """
    4-layer status engine. DB runs on EVERY test, not just as fallback.

    Layer 1 — H/L flag or keyword explicitly printed in the report
    Layer 2 — Numeric math against ref_range printed in the report
              + DB cross-check: if DB disagrees with Layer 2, mark borderline
    Layer 3 — DB only (when report has no printed range)
    Layer 4 — Keep Gemini's original status
    """
    current = (test.get("status") or "normal").lower()
    if current == "info":
        return test

    val_str  = str(test.get("value", "")).strip()
    flag_str = str(test.get("flag",  "")).strip().upper()
    combined = f"{val_str} {flag_str}".upper()
    test_name = test.get("name", "")

    # ── Layer 1: explicit flag / keyword in report ───────────────────────────
    if flag_str == "H" or re.search(r'\b(HIGH|ELEVATED|ABOVE NORMAL|INCREASED)\b', combined):
        test["status"] = "high"
        _enrich_from_db(test, test_name, gender, age)
        return test
    if flag_str == "L" or re.search(r'\b(LOW|DECREASED|BELOW NORMAL|REDUCED|DEFICIENT)\b', combined):
        test["status"] = "low"
        _enrich_from_db(test, test_name, gender, age)
        return test
    if re.search(r'\d\s*H\b', combined):
        test["status"] = "high"
        _enrich_from_db(test, test_name, gender, age)
        return test
    if re.search(r'\d\s*L\b', combined):
        test["status"] = "low"
        _enrich_from_db(test, test_name, gender, age)
        return test

    # ── Parse numeric value ───────────────────────────────────────────────────
    nums = re.findall(r"[\d.]+", val_str)
    if not nums:
        # No numeric value — still try DB for qualitative enrichment
        _enrich_from_db(test, test_name, gender, age)
        return test
    try:
        val = float(nums[0])
    except ValueError:
        return test

    # ── Always run DB lookup first to get correct expected range ─────────────
    db_status  = db_check_status(test_name, val, gender=gender, age=age)
    db_ref     = get_reference(test_name, gender=gender, age=age)

    # ── Layer 2: ref_range printed in this report ────────────────────────────
    ref = (test.get("ref_range") or "").replace("\u2013", "-").replace("\u2014", "-")
    ref_clean = re.sub(r"[a-zA-Z%/\xb5\s]+$", "", ref).strip()
    range_m = re.search(r"([\d.]+)\s*-\s*([\d.]+)", ref_clean)
    lt_m    = re.search(r"<\s*=?\s*([\d.]+)", ref_clean)
    gt_m    = re.search(r">\s*=?\s*([\d.]+)", ref_clean)

    report_has_range = bool(range_m or lt_m or gt_m)

    if report_has_range:
        # Calculate status from printed range
        if range_m:
            lo, hi = float(range_m.group(1)), float(range_m.group(2))
            margin = (hi - lo) * 0.05
            if val < lo:
                report_status = "low"
            elif val > hi:
                report_status = "high"
            elif val <= lo + margin or val >= hi - margin:
                report_status = "borderline"
            else:
                report_status = "normal"
        elif lt_m:
            report_status = "normal" if val < float(lt_m.group(1)) else "high"
        else:
            report_status = "normal" if val > float(gt_m.group(1)) else "low"

        test["status"] = report_status

        # DB cross-check: if DB says high/low but report says normal → borderline
        if db_status not in ("unknown", "normal") and report_status == "normal":
            test["status"] = "borderline"
            test["_db_note"] = f"DB suggests {db_status} — verify with doctor"

        # Always fill DB clinical note if available
        if db_ref and db_ref.get("note"):
            test["_clinical_note"] = db_ref["note"]

        return test

    # ── Layer 3: no printed range — use DB entirely ──────────────────────────
    if db_status != "unknown":
        test["status"] = db_status
        if db_ref:
            # Fill in the reference range from DB so it shows in the table
            lo_db = db_ref["ref_min"]
            hi_db = db_ref["ref_max"]
            u_db  = db_ref["unit"]
            test["ref_range"]   = f"{lo_db} – {hi_db} {u_db}".strip()
            test["_ref_source"] = "database"
            if db_ref.get("note"):
                test["_clinical_note"] = db_ref["note"]
        return test

    # ── Layer 4: keep Gemini status ───────────────────────────────────────────
    return test


def _enrich_from_db(test: dict, test_name: str, gender: str, age: int) -> None:
    """Fill in missing ref_range and clinical note from DB without changing status."""
    ref = (test.get("ref_range") or "").strip()
    if not ref or ref in ("Not specified", "N/A", ""):
        db_ref = get_reference(test_name, gender=gender, age=age)
        if db_ref:
            lo = db_ref["ref_min"]
            hi = db_ref["ref_max"]
            u  = db_ref["unit"]
            test["ref_range"]   = f"{lo} – {hi} {u}".strip()
            test["_ref_source"] = "database"
            if db_ref.get("note"):
                test["_clinical_note"] = db_ref["note"]


def filter_metadata(data: dict) -> dict:
    """Remove any admin/patient rows that ended up in test_categories."""
    for cat in data.get("test_categories", []):
        cat["tests"] = [
            t for t in cat.get("tests", [])
            if not _is_metadata(t.get("name", ""), t.get("value", ""))
        ]
    data["test_categories"] = [
        c for c in data.get("test_categories", []) if c.get("tests")
    ]
    return data


def validate(data: dict) -> bool:
    keys = ["patient_info", "test_categories", "abnormal_findings"]
    if not all(k in data for k in keys):
        return False
    if not isinstance(data["test_categories"], list):
        return False
    total = sum(len(c.get("tests", [])) for c in data["test_categories"])
    return total > 0


def calc_risk(data: dict) -> dict:
    score = 0
    factors = []
    for cat in data.get("test_categories", []):
        for t in cat.get("tests", []):
            s = (t.get("status") or "normal").lower()
            n = t.get("name", "")
            v = t.get("value", "")
            u = t.get("unit", "")
            if s == "high":
                score += 2; factors.append(f"High {n}: {v} {u}".strip())
            elif s == "low":
                score += 1; factors.append(f"Low {n}: {v} {u}".strip())
            elif s == "abnormal":
                score += 2; factors.append(f"Abnormal {n}: {v}".strip())
            elif s == "borderline":
                score += 1; factors.append(f"Borderline {n}: {v} {u}".strip())
    level = "high" if score >= 8 else ("moderate" if score >= 3 else "low")
    return {"score": score, "level": level, "factors": factors}


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 — GEMINI CALLS
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_age(age_str: str) -> int:
    """Extract integer age from strings like '21 Years', '45', etc."""
    nums = re.findall(r"\d+", str(age_str))
    return int(nums[0]) if nums else 30


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    """
    Truncate extracted text to avoid Gemini token limits.
    Keeps first 80% and last 20% so patient info and totals are preserved.
    """
    if len(text) <= max_chars:
        return text
    keep_start = int(max_chars * 0.80)
    keep_end   = int(max_chars * 0.20)
    middle_msg = f"\n\n... [middle of report truncated — {len(text)-max_chars} chars removed] ...\n\n"
    return text[:keep_start] + middle_msg + text[-keep_end:]


def _gemini_error_message(e: Exception) -> str:
    """Convert Groq/API exceptions into friendly user-facing messages."""
    msg = str(e).lower()
    if "429" in msg or "quota" in msg or "rate" in msg or "rate_limit" in msg:
        return "Groq API rate limit reached. Please wait 30 seconds and try again."
    if "api_key" in msg or "invalid" in msg or "unauthorized" in msg or "401" in msg or "403" in msg:
        return "Invalid API key. Check your API_KEY in the .env file."
    if "timeout" in msg or "deadline" in msg:
        return "Request timed out. The report may be too large — try a clearer image."
    if "safety" in msg or "blocked" in msg or "content_filter" in msg:
        return "Content was blocked by safety filters. Try a different file."
    if "network" in msg or "connection" in msg or "unavailable" in msg:
        return "Network error. Check your internet connection and try again."
    if "model" in msg and "not found" in msg:
        return "AI model not available. Check your Groq account has access to Llama models."
    return f"AI error: {str(e)[:120]}"


def parse_report(text: str, client) -> dict:
    """Call Groq to parse report text → structured dict."""
    # Truncate if too long
    text = _truncate_text(text, max_chars=12000)
    prompt = PARSE_PROMPT.format(text=text)

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1,
            )
            data = json.loads(clean_json(resp.choices[0].message.content))
            data = filter_metadata(data)
            if validate(data):
                # Extract patient gender & age for accurate reference matching
                pi     = data.get("patient_info", {})
                gender = (pi.get("gender") or "male").lower()
                gender = "female" if "f" in gender else "male"
                age    = _parse_age(pi.get("age", "30"))

                # Fix status for every test using 4-layer system
                for cat in data["test_categories"]:
                    cat["tests"] = [fix_status(t, gender=gender, age=age) for t in cat["tests"]]

                # Clean patient name
                name = pi.get("name", "")
                if name:
                    pi["name"] = re.split(r"(?i)\b(UHID|Reg|ID|Age|Sex)\b", name)[0].strip().rstrip("/:,")

                # Attach db_coverage count
                data["_db_coverage"] = sum(
                    1 for cat in data["test_categories"]
                    for t in cat["tests"]
                    if find_test(t.get("name", "")) is not None
                )
                return data
            else:
                log.warning(f"Attempt {attempt+1}: parsed data failed validation")

        except json.JSONDecodeError as e:
            log.warning(f"Attempt {attempt+1}: JSON parse error — {e}")
        except Exception as e:
            err_msg = _gemini_error_message(e)
            log.warning(f"Attempt {attempt+1}: {err_msg}")
            # Don't retry on auth/quota errors — they won't fix themselves
            if any(x in str(e).lower() for x in ["429", "quota", "api_key", "403", "unauthorized"]):
                raise RuntimeError(err_msg)

    return _fallback(text)


def get_insights(data: dict, risk: dict, client) -> dict:
    """Call Groq to generate personalised health insights."""
    pi = data.get("patient_info", {})
    patient_ctx = f"{pi.get('name','Unknown')}, Age {pi.get('age','?')}, {pi.get('gender','?')}"
    report_type = data.get("report_type", "Medical Report")

    all_lines, abnormal_lines, positives = [], [], []
    for cat in data.get("test_categories", []):
        for t in cat["tests"]:
            s = (t.get("status") or "normal").lower()
            line = f"  [{cat['category']}] {t['name']}: {t['value']} {t.get('unit','')} (ref:{t.get('ref_range','N/A')}, status:{s})"
            all_lines.append(line)
            if s == "normal":
                positives.append(f"{t['name']} is within normal range")
            elif s in ["high", "low", "abnormal", "borderline"]:
                abnormal_lines.append(line)

    prompt = INSIGHTS_PROMPT.format(
        patient=patient_ctx,
        report_type=report_type,
        all_tests="\n".join(all_lines) or "None",
        abnormal_tests="\n".join(abnormal_lines) or "  None — all results appear normal",
        risk_score=risk["score"],
        risk_level=risk["level"].upper(),
    )
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.2,
        )
        ins = json.loads(clean_json(resp.choices[0].message.content))
        ins.setdefault("conditions", [])
        ins.setdefault("recommendations", [])
        ins.setdefault("follow_up_tests", ["Repeat any abnormal tests in 3–6 months or as directed by your doctor."])
        ins.setdefault("red_flags", [])
        ins.setdefault("summary", f"Overall risk: {risk['level'].upper()}. Please consult your healthcare provider.")
        ins["positives"] = positives
        ins["risk"] = risk
        return ins
    except json.JSONDecodeError as e:
        log.error(f"Insights JSON parse error: {e}")
        return _fallback_insights(data, risk, positives)
    except Exception as e:
        err_msg = _gemini_error_message(e)
        log.error(f"Insights error: {err_msg}")
        return _fallback_insights(data, risk, positives)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 — FALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

def _fallback(text: str) -> dict:
    lines = text.split("\n")
    tests, name, age, gender = [], "Not specified", "Not specified", "Not specified"
    seen = set()
    for line in lines[:25]:
        if re.search(r"(?i)(mr\.|mrs\.|ms\.|name)", line):
            m = re.search(r"(?:Mr\.|Mrs\.|Ms\.)\s*([A-Za-z\s]{3,30})", line)
            if m: name = m.group(1).strip()
        if re.search(r"(?i)(years?|age)", line):
            m = re.search(r"(\d+)\s*[Yy]", line)
            if m: age = m.group(1) + " Years"
        if re.search(r"(?i)(male|female)", line):
            m = re.search(r"(Male|Female)", line, re.I)
            if m: gender = m.group(1).capitalize()
    for line in lines:
        m = re.search(r"([A-Za-z][A-Za-z0-9\s\(\)/\-\.]{2,35})\s*[:\t]+\s*([\d.]+)\s*([A-Za-z%/µ]*)", line)
        if m:
            tname = m.group(1).strip()
            if tname.lower() not in seen and len(tname) > 2 and not _is_metadata(tname, m.group(2)):
                seen.add(tname.lower())
                tests.append({"name": tname, "value": m.group(2), "unit": m.group(3),
                               "ref_range": "Not specified", "status": "normal", "flag": ""})
    return {
        "report_type": "Unknown — please review manually",
        "patient_info": {"name": name, "age": age, "gender": gender,
                         "report_date": "Not specified", "lab_number": "Not specified",
                         "referring_doctor": "Not specified", "lab_name": "Not specified"},
        "test_categories": [{"category": "Extracted Tests", "tests": tests[:20]}] if tests else [],
        "abnormal_findings": ["Auto-extraction had limited success — review results manually."],
        "critical_values": [],
    }


def _fallback_insights(data: dict, risk: dict, positives: list) -> dict:
    recs, conds = [], []
    for cat in data.get("test_categories", []):
        for t in cat["tests"]:
            s = (t.get("status") or "normal").lower()
            if s in ["high", "low", "abnormal", "borderline"]:
                d = "elevated" if s == "high" else ("low" if s == "low" else s)
                recs.append({"category": "follow-up",
                    "text": f"Your {t['name']} is {d} at {t['value']} {t.get('unit','')} (ref: {t.get('ref_range','N/A')}). Discuss with your doctor.",
                    "priority": "high", "reason": "Outside reference range — clinical review needed."})
                conds.append({"name": f"Abnormal {t['name']}", "probability": "moderate",
                    "evidence": [f"{t['name']}: {t['value']} {t.get('unit','')}"],
                    "explanation": f"Your {t['name']} of {t['value']} {t.get('unit','')} is {d}. Please consult your healthcare provider."})
    if not recs:
        recs.append({"category": "lifestyle",
            "text": "All results appear within normal ranges. Maintain a healthy lifestyle and schedule routine check-ups.",
            "priority": "low", "reason": "No significant abnormalities detected."})
    return {"conditions": conds, "recommendations": recs,
            "follow_up_tests": ["Schedule a routine follow-up with your doctor."],
            "red_flags": [], "positives": positives, "risk": risk,
            "summary": f"Overall risk: {risk['level'].upper()} (score {risk['score']}). " +
                       (f"Contributors: {'; '.join(risk['factors'][:3])}. " if risk["factors"] else "No major risk factors found. ") +
                       "Consult a qualified healthcare professional for personalised advice."}


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — CHARTS
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {"normal": "#2dd4a0", "high": "#ff5c6a", "low": "#ffb547",
          "abnormal": "#ff5c6a", "borderline": "#ffb547", "info": "#5a7090"}


def bar_chart(data: dict) -> Optional[object]:
    if not PLOTLY_OK:
        return None
    xs, ys, cs, hs = [], [], [], []
    for cat in data.get("test_categories", []):
        for t in cat["tests"]:
            s = (t.get("status") or "normal").lower()
            if s == "info": continue
            nums = re.findall(r"[\d.]+", str(t.get("value", "")))
            if not nums: continue
            try:
                v = float(nums[0])
                xs.append(t["name"])
                ys.append(v)
                cs.append(COLORS.get(s, "#3b9eff"))
                hs.append(f"<b>{t['name']}</b><br>Value: {t['value']} {t.get('unit','')}<br>"
                          f"Range: {t.get('ref_range','N/A')}<br>Status: {s.title()}")
            except ValueError:
                pass
    if not xs: return None
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=cs, marker_line_width=0,
                           hovertemplate="%{customdata}<extra></extra>", customdata=hs))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Syne, sans-serif", color="#5a7090", size=11),
        margin=dict(l=0, r=0, t=10, b=90), height=400, bargap=0.35,
        xaxis=dict(tickangle=-45, gridcolor="rgba(99,178,255,0.06)",
                   linecolor="rgba(99,178,255,0.1)", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(99,178,255,0.06)", linecolor="rgba(99,178,255,0.1)"),
        hoverlabel=dict(bgcolor="#141e2e", bordercolor="rgba(99,178,255,0.2)",
                        font=dict(family="Syne", color="#dce8f8", size=12)),
    )
    return fig


def pie_chart(data: dict) -> Optional[object]:
    if not PLOTLY_OK:
        return None
    counts = {}
    for cat in data.get("test_categories", []):
        for t in cat["tests"]:
            s = (t.get("status") or "normal").lower()
            if s == "info": s = "informational"
            counts[s] = counts.get(s, 0) + 1
    if not counts: return None
    labels = list(counts.keys())
    values = [counts[l] for l in labels]
    colors = [COLORS.get(l, "#3b9eff") for l in labels]
    fig = go.Figure(go.Pie(
        labels=[l.title() for l in labels], values=values,
        marker=dict(colors=colors, line=dict(color="#080c12", width=2)),
        hole=0.6, hovertemplate="<b>%{label}</b><br>%{value} tests (%{percent})<extra></extra>",
        textfont=dict(family="Syne", size=12, color="#dce8f8"),
    ))
    total = sum(values)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Syne", color="#5a7090"),
        showlegend=True, legend=dict(font=dict(color="#8fa8c8", size=12), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=10, b=10), height=300,
        annotations=[dict(text=f"<b>{total}</b><br>tests",
                          x=0.5, y=0.5, font=dict(size=16, color="#dce8f8", family="Syne"),
                          showarrow=False)],
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 8 — EXPORT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def make_markdown(data: dict, insights: dict) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rtype = data.get("report_type", "Medical Report")
    pi = data.get("patient_info", {})
    risk = insights.get("risk", {})
    md = f"# MedScan AI — {rtype}\n\n"
    md += f"**Generated:** {ts}  \n**System:** MedScan AI v1.0\n\n"
    md += "---\n\n> ⚠️ **Disclaimer:** For educational purposes only. Always consult a qualified healthcare professional.\n\n---\n\n"
    md += "## Patient Information\n"
    for k, v in pi.items():
        if v and v != "Not specified":
            md += f"**{k.replace('_',' ').title()}:** {v}  \n"
    if risk:
        md += f"\n## Risk Assessment\n**Overall Risk:** {risk.get('level','').upper()}  \n**Score:** {risk.get('score',0)}\n\n"
    md += "\n## Test Results\n"
    for cat in data.get("test_categories", []):
        md += f"\n### {cat.get('category','Tests')}\n"
        md += "| Test | Value | Reference Range | Status |\n|------|-------|-----------------|--------|\n"
        for t in cat.get("tests", []):
            s = t.get("status", "normal")
            sym = {"normal": "✓", "high": "▲", "low": "▼", "abnormal": "✕", "borderline": "~", "info": "ℹ"}.get(s, "")
            md += f"| {t['name']} | {t['value']} {t.get('unit','')} | {t.get('ref_range','N/A')} | {sym} {s.title()} |\n"
    if insights.get("recommendations"):
        md += "\n## Recommendations\n"
        for r in insights["recommendations"]:
            md += f"\n**{r.get('category','').title()} — {r.get('priority','').upper()}**  \n"
            md += f"- {r.get('text','')}  \n"
            if r.get("reason"): md += f"  *{r['reason']}*  \n"
    if insights.get("summary"):
        md += f"\n## Summary\n{insights['summary']}\n"
    md += "\n---\n*This AI analysis is for educational purposes only and does not replace professional medical advice.*\n"
    return md


def make_csv(data: dict) -> str:
    rows = []
    for cat in data.get("test_categories", []):
        for t in cat.get("tests", []):
            rows.append({
                "Category": cat.get("category", ""),
                "Test Name": t.get("name", ""),
                "Value": t.get("value", ""),
                "Unit": t.get("unit", ""),
                "Reference Range": t.get("ref_range", ""),
                "Status": t.get("status", ""),
                "Flag": t.get("flag", ""),
            })
    if not PANDAS_OK:
        # Fallback: plain CSV string without pandas
        lines = ["Category,Test Name,Value,Unit,Reference Range,Status,Flag"]
        for r in rows:
            lines.append(",".join(f'"{str(v)}"' for v in r.values()))
        return "\n".join(lines)
    return pd.DataFrame(rows).to_csv(index=False)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 9 — UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def badge(status: str) -> str:
    s = (status or "normal").lower()
    icons = {"normal": "●", "high": "▲", "low": "▼",
             "abnormal": "✕", "borderline": "~", "info": "ℹ"}
    labels = {"normal": "Normal", "high": "High", "low": "Low",
              "abnormal": "Abnormal", "borderline": "Borderline", "info": "Info"}
    cls = {"normal": "b-normal", "high": "b-high", "low": "b-low",
           "abnormal": "b-abnormal", "borderline": "b-borderline", "info": "b-info"}
    return f'<span class="badge {cls.get(s,"b-normal")}">{icons.get(s,"●")} {labels.get(s,"Normal")}</span>'


def stat_card(label: str, value: str, icon: str, color: str) -> str:
    return f"""<div class="stat" style="--stat-color:{color}">
        <div class="stat-icon">{icon}</div>
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
    </div>"""


def risk_card(label: str, level: str) -> str:
    cls = {"low": "risk-low", "moderate": "risk-mod", "high": "risk-high"}.get(level.lower(), "risk-mod")
    return f"""<div class="risk-card {cls}">
        <div class="risk-label">{label}</div>
        <div class="risk-val">{level.title()}</div>
    </div>"""


def sec_header(title: str, dot_color: str = "var(--blue)") -> str:
    return f"""<div class="sec">
        <div class="sec-dot" style="background:{dot_color}"></div>
        <h3>{title}</h3>
    </div>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 10 — MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(page_title="MedScan AI", page_icon="🔬",
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)

    # ── API KEY ───────────────────────────────────────────────────────────────
    api_key = os.getenv("API_KEY", "")

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px">
          <div style="width:34px;height:34px;background:rgba(59,158,255,.15);
            border:1px solid rgba(59,158,255,.3);border-radius:8px;
            display:flex;align-items:center;justify-content:center;font-size:16px">🔬</div>
          <div>
            <div style="font-size:.95rem;font-weight:800;color:#dce8f8;letter-spacing:-.02em">MedScan AI</div>
            <div style="font-size:.68rem;color:#5a7090">Universal Report Analyzer</div>
          </div>
        </div>""", unsafe_allow_html=True)

        if api_key:
            st.markdown("""<div style="background:rgba(45,212,160,.08);border:1px solid rgba(45,212,160,.2);
              border-radius:8px;padding:8px 12px;font-size:.78rem;color:#2dd4a0;margin-bottom:16px;
              display:flex;align-items:center;gap:6px"><span>●</span>MedScan AI</div>""",
              unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background:rgba(255,92,106,.08);border:1px solid rgba(255,92,106,.2);
              border-radius:8px;padding:8px 12px;font-size:.78rem;color:#ff5c6a;margin-bottom:16px">
              ⚠ API_KEY not found in .env file</div>""", unsafe_allow_html=True)

       

        st.markdown('<div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a7090;margin-bottom:8px">Options</div>', unsafe_allow_html=True)
        do_insights = st.checkbox("AI Health Insights", value=True)
        do_export   = st.checkbox("Export Options", value=True)

        st.markdown('<div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a7090;margin:16px 0 8px">Supported Reports</div>', unsafe_allow_html=True)
        reports = ["CBC / Haematology", "Liver Function (LFT)", "Kidney Function (KFT/RFT)",
                   "Thyroid (TFT)", "Lipid Panel", "Blood Glucose / HbA1c",
                   "Urine Routine + Microscopy", "Stool Analysis",
                   "Culture & Sensitivity", "Coagulation (PT/INR/APTT)",
                   "Iron Studies / Ferritin", "Vitamins & Minerals",
                   "Hormones (FSH/LH/Testosterone)", "Tumour Markers",
                   "Cardiac Markers", "Electrolytes", "Autoimmune Panel", "& many more"]
        for r in reports:
            st.markdown(f'<div style="font-size:.76rem;color:#5a7090;padding:2px 0;display:flex;align-items:center;gap:6px"><span style="color:#3b9eff;font-size:.6rem">●</span>{r}</div>', unsafe_allow_html=True)

        if "data" in st.session_state:
            d = st.session_state.data
            total = sum(len(c["tests"]) for c in d.get("test_categories", []))
            st.markdown(f"""<div style="margin-top:20px;padding-top:14px;border-top:1px solid rgba(99,178,255,.08)">
              <div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a7090;margin-bottom:8px">Current Report</div>
              <div style="background:#141e2e;border:1px solid rgba(99,178,255,.08);border-radius:8px;padding:10px 12px">
                <div style="font-size:.68rem;color:#5a7090;margin-bottom:4px">Report Type</div>
                <div style="font-size:.78rem;font-weight:700;color:#a78bfa">{d.get('report_type','Unknown')}</div>
              </div>
              <div style="background:#141e2e;border:1px solid rgba(99,178,255,.08);border-radius:8px;padding:10px 12px;margin-top:6px">
                <div style="font-size:.68rem;color:#5a7090;margin-bottom:4px">Tests Analysed</div>
                <div style="font-size:1.5rem;font-weight:800;color:#dce8f8">{total}</div>
              </div>
              <div style="background:#141e2e;border:1px solid rgba(45,212,160,.12);border-radius:8px;padding:10px 12px;margin-top:6px">
                <div style="font-size:.68rem;color:#5a7090;margin-bottom:4px">DB Coverage</div>
                <div style="font-size:.88rem;font-weight:700;color:#2dd4a0">{d.get("_db_coverage", 0)} / {total} matched</div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px;padding-top:14px;border-top:1px solid rgba(99,178,255,.08)"><div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a7090;margin-bottom:8px"></div></div>', unsafe_allow_html=True)

        deps = [
           
        ]
        for name, ok, role in deps:
            color  = "#2dd4a0" if ok else "#ff5c6a"
            dot    = "●" if ok else "✕"
            status = "OK" if ok else "missing"
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;font-size:.74rem"><span style="color:#8fa8c8">{name}</span><span style="color:{color};font-weight:700">{dot} {status}</span></div>', unsafe_allow_html=True)

        if not PYMUPDF_OK or not PLOTLY_OK or not PANDAS_OK or not OCR_OK:
            st.markdown('<div style="font-size:.68rem;color:#5a7090;margin-top:6px">Run: <code style="background:#141e2e;padding:1px 4px;border-radius:3px;color:#3b9eff">pip install -r requirements.txt</code></div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top:16px;font-size:.7rem;color:#3a4a60;line-height:1.6;border-top:1px solid rgba(99,178,255,.06);padding-top:12px">For educational purposes only.<br>Always consult a healthcare professional.</div>', unsafe_allow_html=True)

    # ── GUARD: critical libraries missing ────────────────────────────────────
    missing_critical = []
    if not GROQ_OK:
        missing_critical.append(("openai", "pip install openai"))
    if not PIL_OK:
        missing_critical.append(("Pillow", "pip install Pillow"))

    if missing_critical:
        st.markdown("""<div class="app-header">
          <div class="app-logo">🔬</div>
          <div><div class="app-title">MedScan AI</div>
          <div class="app-sub">Universal Medical Report Analyzer</div></div>
        </div>""", unsafe_allow_html=True)
        st.error("⚠️ Some required packages are missing. Run these commands and restart:")
        for pkg, cmd in missing_critical:
            st.code(cmd, language="bash")
        st.info("After installing, restart with: streamlit run app.py")
        return

    # ── GUARD: no API key ─────────────────────────────────────────────────────
    if not api_key:
        st.markdown("""<div class="app-header">
          <div class="app-logo">🔬</div>
          <div><div class="app-title">MedScan AI</div>
          <div class="app-sub">Universal Medical Report Analyzer</div></div>
        </div>""", unsafe_allow_html=True)
        st.error("⚠️ API_KEY not found. Please add your Groq API key to the .env file.")
        st.code("API_KEY=your_groq_api_key_here", language="bash")
        st.info("Get a free Groq key at: https://console.groq.com → API Keys")
        return

    # ── INIT GROQ CLIENT ──────────────────────────────────────────────────────
    try:
        client = GroqClient(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    except Exception as e:
        st.error(f"Failed to initialise Groq client: {e}")
        st.info("Check your API_KEY in the .env file.")
        return

    # ── HEADER ────────────────────────────────────────────────────────────────
    st.markdown("""<div class="app-header">
      <div class="app-logo">🔬</div>
      <div>
        <div class="app-title">MedScan AI</div>
        <div class="app-sub">Upload any medical lab report — blood, urine, culture, thyroid, liver, kidney &amp; more</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="disclaimer">
      ⚠️ <strong>Medical Disclaimer:</strong>&nbsp;
      This tool is for educational purposes only and does not constitute medical advice.
      Always consult a qualified healthcare professional before making any health decisions.
    </div>""", unsafe_allow_html=True)

    # ── UPLOAD ROW ────────────────────────────────────────────────────────────
    col_up, col_stats = st.columns([3, 1], gap="large")

    with col_up:
        st.markdown('<div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a7090;margin-bottom:8px">Upload Report</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop your medical report here — PDF or Image",
            type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"],
            help="Works with any lab report: blood tests, urine, culture, thyroid, lipid, etc.",
            label_visibility="visible",
        )

        if uploaded:
            kb = uploaded.size / 1024
            ext = uploaded.name.split(".")[-1].upper()
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
              background:rgba(45,212,160,.06);border:1px solid rgba(45,212,160,.15);
              border-radius:8px;margin:8px 0;font-size:.84rem">
              <span style="color:#2dd4a0">●</span>
              <span style="color:#dce8f8;font-weight:600">{uploaded.name}</span>
              <span style="background:rgba(59,158,255,.1);color:#3b9eff;font-size:.7rem;
                font-weight:700;padding:2px 8px;border-radius:99px;margin-left:4px">{ext}</span>
              <span style="color:#5a7090;margin-left:auto">{kb:.1f} KB</span>
            </div>""", unsafe_allow_html=True)

            if st.button("🔍  Analyze Report", type="primary", use_container_width=True):
                # File size guard — warn if > 10MB
                if uploaded.size > 10 * 1024 * 1024:
                    st.warning("⚠️ File is larger than 10MB. Large files may be slow or fail. Consider compressing the image.")

                with st.spinner(""):
                    progress_placeholder = st.empty()
                    try:
                        file_bytes = uploaded.read()
                        ext_lower  = uploaded.name.lower().split(".")[-1]

                        # ── STEP 1: Extract text ──────────────────────────
                        progress_placeholder.info("📄 Step 1/3 — Extracting text from report...")
                        if ext_lower == "pdf":
                            text = extract_pdf(file_bytes)
                            if not text.strip():
                                if not PIL_OK:
                                    progress_placeholder.error("❌ PDF has no text layer and Pillow is not installed for image processing.\nRun: pip install Pillow")
                                    return
                                progress_placeholder.warning("📷 No text layer found in PDF — using AI vision (slower)...")
                                text = extract_image(file_bytes, client)
                        else:
                            if not PIL_OK:
                                progress_placeholder.error("❌ Pillow is not installed — cannot process image files.\nRun: pip install Pillow")
                                return
                            text = extract_image(file_bytes, client)
                            if not text.strip() and OCR_OK:
                                progress_placeholder.warning("🔍 Trying OCR fallback...")
                                text = extract_image_ocr(file_bytes)

                        if not text or len(text.strip()) < 30:
                            progress_placeholder.error(
                                "❌ Could not extract readable text from this file.\n\n"
                                "**Try these fixes:**\n"
                                "- Use a clearer, higher-resolution image\n"
                                "- Make sure the image is not rotated or blurry\n"
                                "- For PDFs, ensure the file is not password-protected\n"
                                "- Try saving as JPG or PNG and uploading the image instead"
                            )
                            return

                        # ── STEP 2: Parse ─────────────────────────────────
                        progress_placeholder.info(f"🧠 Step 2/3 — Analysing {len(text):,} characters of report text...")
                        try:
                            data = parse_report(text, client)
                        except RuntimeError as e:
                            # Auth/quota errors from _gemini_error_message
                            progress_placeholder.error(f"❌ {e}")
                            return

                        st.session_state.data = data
                        st.session_state.text = text

                        risk = calc_risk(data)
                        st.session_state.risk = risk

                        # ── STEP 3: Charts ────────────────────────────────
                        st.session_state.bar = bar_chart(data)
                        st.session_state.pie = pie_chart(data)

                        # ── STEP 4: Insights ──────────────────────────────
                        if do_insights:
                            progress_placeholder.info("⚕️ Step 3/3 — Generating personalised health insights...")
                            try:
                                insights = get_insights(data, risk, client)
                            except Exception as e:
                                progress_placeholder.warning(f"⚠️ Insights generation failed ({_gemini_error_message(e)}) — showing report only.")
                                insights = {"conditions": [], "recommendations": [],
                                            "follow_up_tests": [], "red_flags": [],
                                            "positives": [], "risk": risk, "summary": ""}
                        else:
                            insights = {"conditions": [], "recommendations": [],
                                        "follow_up_tests": [], "red_flags": [],
                                        "positives": [], "risk": risk, "summary": ""}
                        st.session_state.insights = insights

                        rtype  = data.get("report_type", "Report")
                        total  = sum(len(c["tests"]) for c in data.get("test_categories", []))
                        db_cov = data.get("_db_coverage", 0)
                        progress_placeholder.success(
                            f"✅ Done! **{rtype}** — {total} tests found, {db_cov} matched in reference DB"
                        )

                    except Exception as e:
                        err = _gemini_error_message(e)
                        progress_placeholder.error(f"❌ {err}")
                        log.error("Analysis error", exc_info=True)

    with col_stats:
        st.markdown('<div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5a7090;margin-bottom:8px">Quick Stats</div>', unsafe_allow_html=True)
        if "data" in st.session_state and "risk" in st.session_state:
            d    = st.session_state.data
            risk = st.session_state.risk
            all_st   = [t.get("status","").lower() for c in d.get("test_categories",[]) for t in c.get("tests",[])]
            total    = len(all_st)
            normal_n = all_st.count("normal")
            high_n   = all_st.count("high")
            low_n    = all_st.count("low")
            abnorm_n = sum(1 for s in all_st if s in ["high","low","abnormal","borderline"])
            rl       = risk.get("level","moderate")
            rc       = {"low":"#2dd4a0","moderate":"#ffb547","high":"#ff5c6a"}.get(rl,"#ffb547")
            st.markdown(f"""<div class="stat-row" style="grid-template-columns:1fr 1fr;gap:8px">
              {stat_card("Total Tests", str(total), "🧪", "#3b9eff")}
              {stat_card("Normal",      str(normal_n), "✓", "#2dd4a0")}
              {stat_card("Abnormal",    str(abnorm_n), "⚠", "#ff5c6a")}
              {stat_card("Risk Level",  rl.title(),    "🎯", rc)}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background:#0e1520;border:1px solid rgba(99,178,255,.08);
              border-radius:10px;padding:2rem 1rem;text-align:center">
              <div style="font-size:1.5rem;opacity:.2;margin-bottom:6px">📊</div>
              <div style="font-size:.78rem;color:#5a7090">Upload a report to see stats</div>
            </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  RESULTS SECTION
    # ══════════════════════════════════════════════════════════════════════════
    if "data" not in st.session_state:
        return

    st.markdown("<hr>", unsafe_allow_html=True)
    d        = st.session_state.data
    risk     = st.session_state.risk
    insights = st.session_state.get("insights", {})
    rtype    = d.get("report_type", "")

    if rtype:
        st.markdown(f'<div class="rtype">🔬 {rtype}</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "  Overview  ", "  Test Results  ", "  Charts  ", "  AI Insights  ", "  Export  "
    ])

    # ── TAB 1: OVERVIEW ───────────────────────────────────────────────────────
    with tab1:
        pi = d.get("patient_info", {})
        fields = [
            ("Patient Name",     pi.get("name",             "Not specified")),
            ("Age",              pi.get("age",              "Not specified")),
            ("Gender",           pi.get("gender",           "Not specified")),
            ("Report Date",      pi.get("report_date",      "Not specified")),
            ("Lab / UHID No.",   pi.get("lab_number",       "Not specified")),
            ("Referring Doctor", pi.get("referring_doctor", "Not specified")),
            ("Laboratory",       pi.get("lab_name",         "Not specified")),
        ]
        visible = [(l, v) for l, v in fields if v and v != "Not specified"] or fields[:5]

        st.markdown(sec_header("Patient Information"), unsafe_allow_html=True)
        cols = st.columns(3)
        for i, (label, value) in enumerate(visible):
            with cols[i % 3]:
                st.markdown(f'<div class="pt-field"><div class="pt-label">{label}</div><div class="pt-value">{value}</div></div>', unsafe_allow_html=True)

        # Summary stats row
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(sec_header("Report Summary"), unsafe_allow_html=True)
        all_st   = [t.get("status","").lower() for c in d.get("test_categories",[]) for t in c.get("tests",[])]
        total    = len(all_st)
        normal_n = all_st.count("normal")
        high_n   = all_st.count("high")
        low_n    = all_st.count("low")
        st.markdown(f"""<div class="stat-row">
          {stat_card("Total Tests",    str(total),    "🧪", "#3b9eff")}
          {stat_card("Normal Results", str(normal_n), "✓",  "#2dd4a0")}
          {stat_card("High Values",    str(high_n),   "▲",  "#ff5c6a")}
          {stat_card("Low Values",     str(low_n),    "▼",  "#ffb547")}
        </div>""", unsafe_allow_html=True)

        # Category breakdown
        cats = d.get("test_categories", [])
        if cats:
            st.markdown(sec_header("Test Categories"), unsafe_allow_html=True)
            ccols = st.columns(min(len(cats), 3))
            for i, cat in enumerate(cats):
                tests_in = cat.get("tests", [])
                abn = sum(1 for t in tests_in if t.get("status","").lower() in ["high","low","abnormal","borderline"])
                color = "#ff5c6a" if abn else "#2dd4a0"
                flag_html = f'<div style="font-size:.72rem;color:#ff5c6a;margin-top:4px">⚠ {abn} abnormal</div>' if abn else '<div style="font-size:.72rem;color:#2dd4a0;margin-top:4px">● All normal</div>'
                with ccols[i % 3]:
                    st.markdown(f"""<div class="stat" style="--stat-color:{color};margin-bottom:8px">
                      <div class="stat-label">{cat.get('category','')}</div>
                      <div style="display:flex;align-items:baseline;gap:6px">
                        <div class="stat-value">{len(tests_in)}</div>
                        <div style="font-size:.75rem;color:#5a7090">tests</div>
                      </div>{flag_html}
                    </div>""", unsafe_allow_html=True)

        # Critical values
        crits = d.get("critical_values", [])
        if crits:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown(sec_header("⚡ Critical Values — Seek Immediate Attention", "#ff5c6a"), unsafe_allow_html=True)
            for cv in crits:
                st.markdown(f'<div class="critical"><span style="font-size:1rem">🚨</span><span class="critical-text">{cv}</span></div>', unsafe_allow_html=True)

    # ── TAB 2: TEST RESULTS ───────────────────────────────────────────────────
    with tab2:
        st.markdown(sec_header("Detailed Test Results"), unsafe_allow_html=True)
        test_cats = d.get("test_categories", [])

        if not test_cats:
            st.markdown('<div style="text-align:center;padding:3rem;color:#5a7090"><div style="font-size:2rem;opacity:.2;margin-bottom:6px">🔬</div>No test categories found.</div>', unsafe_allow_html=True)
        else:
            for i, cat in enumerate(test_cats):
                tests  = cat.get("tests", [])
                cname  = cat.get("category", f"Category {i+1}")
                abn    = sum(1 for t in tests if t.get("status","").lower() in ["high","low","abnormal","borderline"])
                flag   = f"  ⚠ {abn} abnormal" if abn else ""

                with st.expander(f"🔬  {cname}{flag}", expanded=(i == 0)):
                    if not tests:
                        st.markdown('<div style="color:#5a7090;font-size:.84rem">No tests in this category.</div>', unsafe_allow_html=True)
                        continue

                    rows = ""
                    for t in tests:
                        s       = (t.get("status") or "normal").lower()
                        bdg     = badge(s)
                        val_cls = {"high": "v-high", "abnormal": "v-high",
                                   "low": "v-low", "borderline": "v-low"}.get(s, "v-normal")
                        row_cls = f"row-{s}" if s in ["high","low","abnormal","borderline"] else ""
                        note = f'<div class="td-note">{t["flag"]}</div>' if t.get("flag") else ""
                        if t.get("_clinical_note"):
                            note += f'<div style="font-size:.68rem;color:#5a7090;margin-top:2px;font-style:italic">{t["_clinical_note"]}</div>'
                        if t.get("_db_note"):
                            note += f'<div style="font-size:.68rem;color:#ffb547;margin-top:2px">⚠ {t["_db_note"]}</div>'
                        ref_val = t.get("ref_range", "N/A") or "N/A"
                        db_tag  = '<span style="font-size:.58rem;background:rgba(59,158,255,.12);color:#3b9eff;border:1px solid rgba(59,158,255,.2);border-radius:3px;padding:1px 5px;margin-left:5px;vertical-align:middle;font-weight:700">DB</span>' if t.get("_ref_source") == "database" else ""
                        rows += f"""<tr class="{row_cls}">
                          <td class="td-name">{t.get('name','N/A')}{note}</td>
                          <td class="td-val {val_cls}">{t.get('value','N/A')} <span style="color:#5a7090;font-size:.76rem;font-family:Syne,sans-serif">{t.get('unit','')}</span></td>
                          <td class="td-ref">{ref_val}{db_tag}</td>
                          <td>{bdg}</td>
                        </tr>"""

                    st.markdown(f"""<div style="border-radius:10px;overflow:hidden;border:1px solid rgba(99,178,255,.08)">
                      <table class="report-table">
                        <thead><tr>
                          <th>Test Name</th><th>Value</th><th>Reference Range</th><th>Status</th>
                        </tr></thead>
                        <tbody>{rows}</tbody>
                      </table>
                    </div>""", unsafe_allow_html=True)

            # Abnormal findings
            findings = d.get("abnormal_findings", [])
            valid_f  = [f for f in findings if "unable" not in f.lower() and "manual" not in f.lower()]
            if valid_f:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                st.markdown(sec_header("Abnormal Findings Summary", "#ff5c6a"), unsafe_allow_html=True)
                for f in valid_f:
                    icon  = "▲" if "high" in f.lower() or "above" in f.lower() else "▼"
                    cls   = "finding-high" if icon == "▲" else "finding-low"
                    color = "#ff5c6a" if icon == "▲" else "#ffb547"
                    st.markdown(f'<div class="finding {cls}"><span class="finding-icon" style="color:{color}">{icon}</span><span class="finding-text">{f}</span></div>', unsafe_allow_html=True)

    # ── TAB 3: CHARTS ─────────────────────────────────────────────────────────
    with tab3:
        if not PLOTLY_OK:
            st.markdown("""<div style="text-align:center;padding:3rem;background:#0e1520;
              border:1px solid rgba(255,92,106,.15);border-radius:10px">
              <div style="font-size:2rem;margin-bottom:8px">📊</div>
              <div style="font-size:.9rem;color:#ff5c6a;font-weight:600;margin-bottom:6px">Plotly not installed</div>
              <div style="font-size:.8rem;color:#5a7090">Charts are unavailable. Install it with:</div>
              <code style="background:#141e2e;color:#3b9eff;padding:4px 10px;border-radius:4px;
                font-size:.8rem;display:inline-block;margin-top:8px">pip install plotly</code>
              <div style="font-size:.78rem;color:#5a7090;margin-top:8px">All other features still work normally.</div>
            </div>""", unsafe_allow_html=True)
        else:
            c1, c2 = st.columns([2, 1], gap="large")
            with c1:
                st.markdown(sec_header("Numeric Test Values"), unsafe_allow_html=True)
                st.markdown("""<div style="display:flex;gap:16px;margin-bottom:12px;font-size:.76rem">
                  <span style="display:flex;align-items:center;gap:5px;color:#8fa8c8"><span style="width:9px;height:9px;border-radius:50%;background:#2dd4a0;display:inline-block"></span> Normal</span>
                  <span style="display:flex;align-items:center;gap:5px;color:#8fa8c8"><span style="width:9px;height:9px;border-radius:50%;background:#ff5c6a;display:inline-block"></span> High / Abnormal</span>
                  <span style="display:flex;align-items:center;gap:5px;color:#8fa8c8"><span style="width:9px;height:9px;border-radius:50%;background:#ffb547;display:inline-block"></span> Low / Borderline</span>
                </div>""", unsafe_allow_html=True)
                if st.session_state.get("bar"):
                    st.plotly_chart(st.session_state.bar, use_container_width=True)
                else:
                    st.markdown('<div style="text-align:center;padding:3rem;color:#5a7090;background:#0e1520;border:1px solid rgba(99,178,255,.08);border-radius:10px"><div style="font-size:1.5rem;opacity:.2;margin-bottom:6px">📈</div>No numeric data for chart.<br><span style="font-size:.75rem">Qualitative results appear in Test Results tab.</span></div>', unsafe_allow_html=True)

            with c2:
                st.markdown(sec_header("Status Distribution"), unsafe_allow_html=True)
                if st.session_state.get("pie"):
                    st.plotly_chart(st.session_state.pie, use_container_width=True)
                else:
                    st.markdown('<div style="text-align:center;padding:2rem;color:#5a7090;background:#0e1520;border:1px solid rgba(99,178,255,.08);border-radius:10px"><div style="font-size:1.5rem;opacity:.2;margin-bottom:6px">🥧</div>No data</div>', unsafe_allow_html=True)

    # ── TAB 4: AI INSIGHTS ────────────────────────────────────────────────────
    with tab4:
        if not insights or not insights.get("recommendations"):
            st.markdown('<div style="text-align:center;padding:3rem;color:#5a7090"><div style="font-size:2rem;opacity:.2;margin-bottom:6px">⚕️</div>Enable "AI Health Insights" in the sidebar and re-analyze to see insights.</div>', unsafe_allow_html=True)
        else:
            # Red flags first
            for rf in insights.get("red_flags", []):
                st.markdown(f'<div class="critical"><span style="font-size:1.1rem">🚨</span><span class="critical-text">{rf}</span></div>', unsafe_allow_html=True)

            # Risk grid
            rl = risk.get("level", "moderate")
            st.markdown(sec_header("Risk Assessment"), unsafe_allow_html=True)
            rcols = st.columns(3)
            with rcols[0]: st.markdown(risk_card("Overall Risk", rl), unsafe_allow_html=True)
            with rcols[1]: st.markdown(risk_card("Risk Score", f"{risk.get('score',0)} pts"), unsafe_allow_html=True)
            with rcols[2]:
                abn_count = len([t for c in d.get("test_categories",[]) for t in c.get("tests",[]) if t.get("status","").lower() in ["high","low","abnormal","borderline"]])
                abn_level = "high" if abn_count >= 5 else ("moderate" if abn_count >= 2 else "low")
                st.markdown(risk_card("Flagged Tests", str(abn_count)), unsafe_allow_html=True)

            # Risk factors
            if risk.get("factors"):
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown(sec_header("Risk Contributors", "#ff5c6a"), unsafe_allow_html=True)
                for f in risk["factors"]:
                    st.markdown(f'<div class="finding finding-high"><span class="finding-icon" style="color:#ff5c6a">▲</span><span class="finding-text">{f}</span></div>', unsafe_allow_html=True)

            # Conditions
            if insights.get("conditions"):
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown(sec_header("Conditions to Discuss with Your Doctor", "#a78bfa"), unsafe_allow_html=True)
                for cond in insights["conditions"]:
                    prob = cond.get("probability", "moderate")
                    pc   = {"low": "#2dd4a0", "moderate": "#ffb547", "high": "#ff5c6a"}.get(prob, "#ffb547")
                    pb   = {"low": "rgba(45,212,160,.08)", "moderate": "rgba(255,181,71,.08)", "high": "rgba(255,92,106,.08)"}.get(prob, "rgba(255,181,71,.08)")
                    pbd  = {"low": "rgba(45,212,160,.2)", "moderate": "rgba(255,181,71,.2)", "high": "rgba(255,92,106,.2)"}.get(prob, "rgba(255,181,71,.2)")
                    evid = "".join(f'<div style="font-size:.74rem;color:#5a7090;margin-top:3px">· {e}</div>' for e in cond.get("evidence", []))
                    st.markdown(f"""<div style="background:{pb};border:1px solid {pbd};border-radius:10px;padding:12px 16px;margin-bottom:8px">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                        <div style="font-size:.9rem;font-weight:700;color:#dce8f8">{cond.get('name','')}</div>
                        <span style="font-size:.7rem;font-weight:700;color:{pc};padding:2px 10px;background:rgba(255,255,255,.04);border-radius:99px">{prob.title()} probability</span>
                      </div>
                      <div style="font-size:.82rem;color:#8fa8c8;line-height:1.55">{cond.get('explanation','')}</div>
                      {evid}
                    </div>""", unsafe_allow_html=True)

            # Recommendations
            if insights.get("recommendations"):
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown(sec_header("Personalised Recommendations", "#3b9eff"), unsafe_allow_html=True)
                cat_map = {}
                for rec in insights["recommendations"]:
                    c = rec.get("category", "general").replace("_", "-").title()
                    cat_map.setdefault(c, []).append(rec)
                icons = {"Lifestyle":"🏃","Dietary":"🥗","Medical":"⚕️",
                         "Follow-Up":"📅","Urgent":"🚨","General":"📌"}
                for cat_name, recs in cat_map.items():
                    st.markdown(f'<div style="font-size:.76rem;font-weight:700;color:#8fa8c8;margin:14px 0 6px;display:flex;align-items:center;gap:6px">{icons.get(cat_name,"●")} {cat_name}</div>', unsafe_allow_html=True)
                    for rec in recs:
                        pri = rec.get("priority", "medium")
                        st.markdown(f"""<div class="rec">
                          <div class="rec-dot p-{pri}"></div>
                          <div class="rec-body">
                            <div class="rec-text">{rec.get('text','')}</div>
                            {f'<div class="rec-why">{rec["reason"]}</div>' if rec.get("reason") else ""}
                          </div>
                        </div>""", unsafe_allow_html=True)

            # Follow-up tests
            if insights.get("follow_up_tests"):
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown(sec_header("Recommended Follow-Up Tests", "#ffb547"), unsafe_allow_html=True)
                for fu in insights["follow_up_tests"]:
                    st.markdown(f'<div class="followup"><span style="color:#ffb547;font-size:.85rem">📅</span><span class="followup-text">{fu}</span></div>', unsafe_allow_html=True)

            # Positive findings
            if insights.get("positives"):
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown(sec_header("Positive Health Indicators", "#2dd4a0"), unsafe_allow_html=True)
                for p in insights["positives"][:10]:
                    st.markdown(f'<div class="positive"><span style="color:#2dd4a0;font-size:.78rem">●</span><span class="positive-text">{p}</span></div>', unsafe_allow_html=True)

            # Summary
            if insights.get("summary"):
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown(f"""<div class="summary-box">
                  <div class="summary-label">Summary</div>
                  <div class="summary-text">{insights['summary']}</div>
                </div>""", unsafe_allow_html=True)

    # ── TAB 5: EXPORT ─────────────────────────────────────────────────────────
    with tab5:
        if not do_export:
            st.info("Enable 'Export Options' in the sidebar to access downloads.")
        else:
            st.markdown(sec_header("Download Your Report"), unsafe_allow_html=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            e1, e2, e3 = st.columns(3, gap="medium")

            md_report = make_markdown(d, insights)
            csv_data  = make_csv(d)
            json_data = json.dumps({"report": d, "insights": insights,
                                    "risk": risk, "generated": datetime.now().isoformat()}, indent=2)

            with e1:
                st.markdown('<div class="exp-card"><div class="exp-icon">📝</div><div class="exp-title">Markdown Report</div><div class="exp-sub">Full analysis with formatting</div></div>', unsafe_allow_html=True)
                st.download_button("Download .md", md_report, f"medscan_{ts}.md", "text/markdown", use_container_width=True)

            with e2:
                st.markdown('<div class="exp-card"><div class="exp-icon">📊</div><div class="exp-title">CSV Spreadsheet</div><div class="exp-sub">All test results as table</div></div>', unsafe_allow_html=True)
                st.download_button("Download .csv", csv_data, f"medscan_{ts}.csv", "text/csv", use_container_width=True)

            with e3:
                st.markdown('<div class="exp-card"><div class="exp-icon">🗂️</div><div class="exp-title">JSON Data</div><div class="exp-sub">Raw structured data</div></div>', unsafe_allow_html=True)
                st.download_button("Download .json", json_data, f"medscan_{ts}.json", "application/json", use_container_width=True)

            # Full report preview
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            with st.expander("👁  Preview Full Report", expanded=False):
                st.markdown(md_report)


if __name__ == "__main__":
    main()