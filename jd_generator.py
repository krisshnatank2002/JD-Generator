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

    # Fallback for local development if not using st.secrets

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    if not GROQ_API_KEY:

        raise RuntimeError("GROQ_API_KEY not found in Streamlit Secrets or Environment Variables")
 
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

    "Technical Exposure",

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

    urgency = None
 
    for col in row.index:

        col_lower = col.lower()

        if "salary" in col_lower:

            value = str(row[col]).strip()

            if value:

                salary = value

        if "urgent" in col_lower or "joining" in col_lower:

            value = str(row[col]).strip()

            if value:

                urgency = value
 
    add_heading(doc, "Compensation & Joining")

    add_paragraph(doc, f"CTC: {salary}" if salary else "CTC: As per company standards")

    add_paragraph(doc, f"Joining: {urgency}" if urgency else "Joining: As per mutual availability")
 
# =====================================================

# HEADER BLOCK

# =====================================================

def build_header_block(row):

    parts = []

    for key in row.index:

        k_low = key.lower()

        if "location" in k_low or "employment" in k_low or "work mode" in k_low or "workmode" in k_low:

            parts.append(str(row[key]))
 
    travel = str(row.get("Does this role require travel?", "")).strip()

    if travel and travel.lower() not in ["no", "none", "nan"]:

        parts.append(f"{travel} travel")
 
    return " | ".join([p for p in parts if p and p != "nan"])
 
# =====================================================

# CORE JD GENERATION (TARGETED INTENT)

# =====================================================

def generate_ranked_jd(row, clarifications=None):

    # Prepare Inputs

    job_title_col = next((k for k in row.index if "job" in k.lower() and "title" in k.lower()), None)

    job_title = to_title_case(row.get(job_title_col, "Untitled Role"))

    clarifications_text = ""

    if clarifications:

        clarifications_text = "\n".join([f"- {q}: {a}" for q, a in clarifications.items() if str(a).lower() not in ["none of the above", "not applicable"]])
 
    # THE PROMPT: Engineered to capture the Recruiter's Motive

    prompt = f"""

ACT AS: A Modern Talent Strategist and "Maker" Recruiter. 

PHILOSOPHY: At WOGOM, we don't just hire for functions; we hire for impact. We want builders who re-architect how work happens. 

MOTIVE: Focus on execution, speed, and automation. If a task can be automated, it should be.
 
ROLE TO GENERATE: {job_title}
 
STRICT OUTPUT RULES:

- Use EXACT section headings provided below.

- NO HALLUCINATIONS: Do not add extra sections or boilerplate text outside the requested headings.

- TONE: High-velocity, outcome-oriented, and "Maker" focused.
 
=====================

REQUIRED STRUCTURE

=====================
 
Role Title

{job_title}
 
About WOGOM

{ABOUT_WOGOM_TEXT}
 
Role Overview

Write a 3-4 line paragraph. Focus on why this role exists to drive efficiency and enablement. Avoid generic filler; emphasize high-impact outcomes.
 
What You'll Do?

Describe execution and ownership (2-3 lines).

Then list 5 high-impact bullet points:

• Focus on "building," "owning," and "re-architecting" workflows.

• Include cross-functional impact and scaling.

• Frame tasks as "deploying solutions" rather than "performing duties."
 
Who’ll Succeed in this Role?

Write 2-3 lines describing the personality:

• Must mention: "Independent, structured, and outcome-oriented."

• Must mention: "Learns fast, experiments faster, iterates fastest."

• Frame them as a "Maker" who obsessed with automation and speed.
 
Must-Have Skills

• Bullet points focusing on workflow mapping and core execution skills.
 
Technical Exposure

• List the technical stack, tools, or automation patterns relevant to this role (e.g., Python, SQL, AI Assistants, or specific industry tools).
 
=====================

INPUT DATA

=====================

Job Title: {job_title}

Core Responsibility: {row.get('What is the single core responsibility of this role?', 'Not Provided')}

Key Responsibilities: {row.get('Key Responsibilities', 'Not Provided')}

Skills Required: {row.get('Top 3 skills this role MUST have', 'Not Provided')}

Recruiter Clarifications: {clarifications_text}

"""
 
    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content.strip()
 
# =====================================================

# CLEANING & WRITING TO DOCX

# =====================================================

def clean_llm_output(jd_text: str) -> list[str]:

    banned_phrases = {"required structure", "input data", "strict output rules", "====================="}

    cleaned_lines = []

    for line in jd_text.split("\n"):

        stripped = line.strip()

        if not stripped or any(b in stripped.lower() for b in banned_phrases) or set(stripped) == {"="}:

            continue

        cleaned_lines.append(stripped)

    return cleaned_lines
 
def write_jd_to_docx(jd_text, row):

    doc = Document()

    # Header block

    job_title_value = to_title_case(str(row.get("Job Title", row.get("__job_title__", "JD"))))

    add_job_title(doc, job_title_value)

    meta = build_header_block(row)

    if meta:

        add_paragraph(doc, meta)
 
    lines = clean_llm_output(jd_text)

    current_section = None
 
    for line in lines:

        if line == "Role Title" or line == job_title_value:

            continue
 
        if line in HEADINGS:

            add_heading(doc, line)

            current_section = line

            if line == "About WOGOM":

                add_paragraph(doc, ABOUT_WOGOM_TEXT)

                current_section = None

            continue
 
        if current_section is None:

            continue
 
        if line.startswith("•") or line.startswith("- "):

            clean_bullet = line.lstrip("•- ").strip()

            add_bullet(doc, clean_bullet)

        else:

            add_paragraph(doc, line)
 
    add_ctc_and_joining(doc, row)

    return doc
 
