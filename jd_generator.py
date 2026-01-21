# jd_generator.py

import os
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import streamlit as st

# =====================================================
# FONT SIZES
# =====================================================
TITLE_FONT_SIZE = Pt(14)
HEADING_FONT_SIZE = Pt(12)
BODY_FONT_SIZE = Pt(10)

# =====================================================
# LOAD GROQ API KEY
# =====================================================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except KeyError:
    raise RuntimeError("GROQ_API_KEY not found in Streamlit Secrets")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=GROQ_API_KEY
)

# =====================================================
# TITLE CASE HELPER
# =====================================================
def to_title_case(title: str) -> str:
    if not title:
        return title
    words = title.split()
    return " ".join(w.upper() if w.lower() == "ai" else w.capitalize() for w in words)
# =====================================================
# CONSTANT COMPANY DESCRIPTION (LOCKED)
# =====================================================
ABOUT_WOGOM_TEXT = (
    "WOGOM is a B2B Commerce and Retail Enablement Platform, empowering 6,000+ retailers "
    "and 450+ sellers across India with better Products, Pricing, Credit, and Growth Opportunities. "
    
    "Our goal is to build a connected ecosystem where technology, capital, and commerce converge "
    "to help Indian retailers scale with confidence."
)

# =====================================================
# JD HEADINGS
# =====================================================
HEADINGS = {
    "Reporting To",
    "About WOGOM",
    "Role Overview",
    "What You’ll Do?",
    "What You'll Do?",
    "Who’ll Succeed in this Role?",
    "Who'll Succeed in this Role?",
    "Must-Have Skills",
    "Preferred Skills",
    "Hiring Priority",
}

# =====================================================
# DOCX HELPERS
# =====================================================
def remove_numbering(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    numPr = pPr.find(qn("w:numPr"))
    if numPr is not None:
        pPr.remove(numPr)

def add_job_title(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = TITLE_FONT_SIZE

def add_heading(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = HEADING_FONT_SIZE
    remove_numbering(p)

def add_paragraph(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = BODY_FONT_SIZE
    remove_numbering(p)

def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    r.font.size = BODY_FONT_SIZE
    
def add_bold_label(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = BODY_FONT_SIZE

# =====================================================
# CTC & JOINING BLOCK (MANDATORY)
# =====================================================
def add_ctc_and_joining(doc, row):
    salary = None
    joining = None

    for col in row.index:
        col_lower = col.lower()
        value = str(row[col]).strip()

        if not value:
            continue

        # Salary column
        if "salary range" in col_lower:
            salary = value

        # Urgency / joining column
        if "urgent" in col_lower or "hire" in col_lower:
            joining = value

    add_heading(doc, "Compensation & Joining")

    add_paragraph(
        doc,
        f"CTC: {salary}" if salary else "CTC: As per company standards"
    )

    add_paragraph(
        doc,
        f"Joining: {joining}" if joining else "Joining: As per mutual availability"
    )

# =====================================================
# HEADER BLOCK
# =====================================================
def build_header_block(row):
    parts = []

    for key in row.index:
        if "location" in key.lower():
            parts.append(row[key])
        if "employment" in key.lower():
            parts.append(row[key])
        if "work mode" in key.lower() or "workmode" in key.lower():
            parts.append(row[key])

    travel = row.get("Does this role require travel?", "").strip()
    if travel:
        parts.append(f"{travel} travel")

    return " | ".join([p for p in parts if p])

# =====================================================
# CLARIFICATION SANITIZER
# =====================================================
def sanitize_clarifications(clarifications):
    """
    Keeps your OLD clarification structure.
    If user selected 'None of the above' / 'Not Applicable',
    that clarification is REMOVED so it does NOT affect the JD.
    """
    sanitized = {}
    for question, answer in clarifications.items():
        if isinstance(answer, str):
            if answer.strip().lower() in ["not applicable", "none of the above"]:
                continue
            sanitized[question] = answer
    return sanitized

# =====================================================
# CORE JD GENERATION
# =====================================================
def generate_ranked_jd(row, clarifications=None):

    clarifications = clarifications or {}
    clarifications = sanitize_clarifications(clarifications)

    job_title_col = next(
        (k for k in row.index if "job" in k.lower() and "title" in k.lower()),
        None
    )

    job_title = to_title_case(row.get(job_title_col, ""))
    clarification_text = ""
    if clarifications:
        clarification_text = "\n".join(
            f"- {q}: {a}" for q, a in clarifications.items()
        )

    prompt = f"""
STRICT OUTPUT RULES (MANDATORY):
- Write in the SAME language quality, tone, and sentence style as a modern
  operator-led startup JD (execution-focused, crisp, non-generic)
- Use short, confident sentences
- Avoid buzzwords, fluff, and corporate clichés
- Sound like the role owner wrote this JD, not HR

STRUCTURE RULES:
- Use EXACT section headings provided
- Do NOT add or remove sections
- Do NOT create a separate Clarifications section
- Clarifications MUST be absorbed naturally
- NEVER mention the word "clarification"

=====================
REQUIRED STRUCTURE
=====================

Role Title
{job_title}

About WOGOM
{ABOUT_WOGOM_TEXT}

Role Overview
Write a clear 2–3 line paragraph.
Explain:
1) Why this role exists
2) How value is created
3) Where the impact is felt
NO bullets. NO skills. NO responsibilities here.


What You'll Do?
First write a short 2–3 max line paragraph describing execution ownership and scope.

Then list 4–5 responsibilities:
• Each bullet must describe a tangible output or action
• Each bullet max 1–2 lines
• Action-oriented, specific, non-generic

Who’ll Succeed in this Role?
Write a 2–3 line max paragraph describing mindset, working style, and ownership.
Do NOT list skills here.
Education and experience must be reflected naturally, not as a list.
Must-Have Skills
• Skill – one-line explanation
• Skill – one-line explanation

Preferred Skills
• Skill – one-line explanation
• Skill – one-line explanation
=====================
CONTEXT TO INCORPORATE (DO NOT DISPLAY)
=====================
The following answers are CONFIRMED and must be naturally reflected
inside the most relevant sections above:

{clarification_text}

=====================
INPUT DATA
=====================

Job Title: {row.get('Job Title','')}
Core Responsibility: {row.get('What is the single core responsibility of this role?','')}
Key Responsibilities: {row.get('Key Responsibilities','')}
Top Skills: {row.get('Top 3 skills this role MUST have','')}
Minimum Education: {row.get('Minimum education required','')}
Minimum Experience: {row.get('Minimum experience required','')}
Other Skills: {row.get('other skills','')}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
    
def clean_llm_output(jd_text: str) -> list[str]:
    """
    Removes prompt scaffolding like:
    =====================
    REQUIRED STRUCTURE
    INPUT DATA
    etc.
    Returns clean JD lines only.
    """
    banned_phrases = {
        "required structure",
        "input data",
        "strict output rules"
    }

    cleaned_lines = []

    for line in jd_text.split("\n"):
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Skip separators like ========
        if set(stripped) == {"="}:
            continue

        # Skip instructional headings
        if stripped.lower() in banned_phrases:
            continue

        cleaned_lines.append(stripped)

    return cleaned_lines

# =====================================================
# WRITE JD TO DOCX
# ======================================================
def write_jd_to_docx(jd_text, row):
    doc = Document()

    # Job title (ONLY ONCE)
    add_job_title(doc, to_title_case(row["__job_title__"]))

    meta = build_header_block(row)
    if meta:
        add_paragraph(doc, meta)

    lines = clean_llm_output(jd_text)
    current_section = None
    job_title_value = to_title_case(row["__job_title__"])

    for line in lines:

        # Skip role title label
        if line == "Role Title":
            continue

        # Skip duplicated job title value
        if line == job_title_value:
            continue

        # Headings
        if line in HEADINGS:
            add_heading(doc, line)
            current_section = line

            # Lock About WOGOM
            if line == "About WOGOM":
                add_paragraph(doc, ABOUT_WOGOM_TEXT)
                current_section = None
            continue

        # Ignore LLM content for locked sections
        if current_section is None:
            continue

        # Bullet points
        if line.startswith("•"):
            add_bullet(doc, line.lstrip("• ").strip())
            continue

        # Normal paragraph
        add_paragraph(doc, line)

    add_ctc_and_joining(doc, row)
    return doc
