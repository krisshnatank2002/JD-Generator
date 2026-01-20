# jd_generator.py

import os
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# =====================================================
# FONT SIZES
# =====================================================
TITLE_FONT_SIZE = Pt(15)
HEADING_FONT_SIZE = Pt(13)
BODY_FONT_SIZE = Pt(11)

# =====================================================
# ==========================================
# LOAD GROQ API KEY (STREAMLIT CLOUD SAFE)
# ==========================================
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
# JD HEADINGS
# =====================================================
HEADINGS = {
    "Reporting To",
    "Role Overview",
    "What You’ll Do?",
    "What You'll Do?",
    "Responsibilities",
    "Requirements",
    "Who’ll Succeed in this Role?",
    "Who'll Succeed in this Role?",
    "Must-Have Skills",
    "Preferred Skills",
    "Growth Opportunities",
    "About WOGOM",
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

# =====================================================
# HEADER BLOCK
# =====================================================
def build_header_block(row):
    parts = []

    for key in ["Location", "Employment Type", "Work mode"]:
        v = row.get(key, "").strip()
        if v:
            parts.append(v)

    travel = row.get("Does this role require travel?", "").strip()
    if travel:
        parts.append(f"{travel} travel")

    return " | ".join(parts)

# =====================================================
# 🔹 NEW: CLARIFICATION SANITIZER (KEY CHANGE)
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
                continue  # 🚫 do not pass to LLM
            sanitized[question] = answer

    return sanitized

# =====================================================
# CORE JD GENERATION (WITH CLARIFICATIONS)
# =====================================================
def generate_ranked_jd(row, clarifications=None):
    """
    Clarifications are MANDATORY if provided.
    They OVERRIDE assumptions and must influence:
    - Responsibilities
    - Requirements
    - Skills
    - Seniority

    If clarification == 'Not Applicable', it is ignored.
    """

    clarifications = clarifications or {}
    clarifications = sanitize_clarifications(clarifications)

    clarification_block = ""
    if clarifications:
        clarification_block = """
IMPORTANT – MANDATORY OVERRIDE RULES:

You MUST strictly incorporate ALL clarifications below.
These clarifications OVERRIDE assumptions from input data.
They MUST directly affect responsibilities, scope, skills, and expectations.

HIRING MANAGER CLARIFICATIONS:
"""
        for q, a in clarifications.items():
            clarification_block += f"- {q}: {a}\n"

    prompt = f"""
{clarification_block}

STRICT FORMATTING RULES:

Role Title section:
- Output ONLY: "Role Title" heading followed by the job title.
- DO NOT include location, travel, or meta info.

Skills sections:
- Must-Have Skills and Preferred Skills MUST be bullet points starting with •
- Each bullet = Skill name + VERY brief explanation (1 line)

If a clarification is not provided, DO NOT infer or assume details for it.

=====================
REQUIRED STRUCTURE
=====================

Role Title
<Job Title Only>

Role Overview
<1 clear paragraph explaining the role's purpose and impact.>

What You'll Do?
<2–3 line intro paragraph describing overall responsibilities.>

Responsibilities
• Write 5–6 responsibilities
• Each responsibility 1–2 lines
• Reflect clarifications explicitly

Requirements
• 4–5 requirements
• Education, experience, seniority must reflect clarifications

Who'll Succeed in this Role?
<1 paragraph describing mindset, ownership, pace, attitude>

Must-Have Skills
• Skill – brief explanation
• Skill – brief explanation
• Skill – brief explanation
• Skill – brief explanation
• Skill – brief explanation

Preferred Skills
• Skill – brief explanation
• Skill – brief explanation
• Skill – brief explanation
• Skill – brief explanation
• Skill – brief explanation

About WOGOM
<2–3 lines about company mission and culture>

=====================
INPUT DATA
=====================

Job Title: {row.get('Job Title','')}

Reporting To: {row.get('Reporting To','')}

Role Overview:
{row.get('Role Overview','')}

Education: {row.get('Minimum education required','')}
Experience: {row.get('Minimum experience required','')}
Core Responsibility: {row.get('What is the single core responsibility of this role?','')}

Key Responsibilities:
{row.get('Key Responsibilities','')}

Top Skills:
{row.get('Top 3 skills this role MUST have','')}

Other Skills:
{row.get('other skills','')}

Growth Opportunities:
{row.get('Growth opportunities in this role','')}

Company Context:
{row.get('Role Context','')}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

# =====================================================
# WRITE JD TO DOCX
# =====================================================
def write_jd_to_docx(jd_text, row):
    doc = Document()

    BULLET_SECTIONS = {
        "Responsibilities",
        "Requirements",
        "Must-Have Skills",
        "Preferred Skills",
    }

    # Job title
    add_job_title(doc, row.get("Job Title", ""))

    # Meta line
    meta = build_header_block(row)
    if meta:
        add_paragraph(doc, meta)

    # Parse JD
    lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
    current_section = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip Role Title section from LLM
        if line == "Role Title":
            i += 2
            continue

        if line in HEADINGS:
            add_heading(doc, line)
            current_section = line
            i += 1
            continue

        if line.startswith(("•", "-", "*")):
            clean = line.lstrip("•-* ").strip()
            if current_section in BULLET_SECTIONS:
                add_bullet(doc, clean)
            else:
                add_paragraph(doc, clean)
            i += 1
            continue

        add_paragraph(doc, line)
        i += 1

    return doc

