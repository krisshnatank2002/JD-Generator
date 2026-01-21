from langchain_core.messages import HumanMessage
import json


def generate_role_specific_clarifying_questions(llm, row, draft_jd: str = ""):
    """
    Generates high-quality clarifying questions for JD creation
    by analyzing BOTH:
    - Excel intake data
    - Draft Job Description (if provided)

    Questions are asked ONLY where:
    - Information is missing
    - Assumptions are made
    - Excel and JD conflict
    - JD could be misleading
    """

    # ----------------------------
    # Resolve Job Title
    # ----------------------------
    job_title = "This role"
    for k in row.index:
        if "job" in k.lower() and "title" in k.lower():
            job_title = str(row[k]).strip()
            break

    # ----------------------------
    # Raw form context (Excel)
    # ----------------------------
    form_context = "\n".join(
        f"{k}: {row[k]}" for k in row.index if str(row[k]).strip()
    )

    questions = []

    # =====================================================
    # 1️⃣ FIXED QUESTION — JOB TITLE REFINEMENT
    # =====================================================
    title_prompt = f"""
You are an HR expert.

Current job title:
"{job_title}"

Generate 5–6 professional alternative job titles
suitable for hiring and job postings.

Rules:
- Keep the same role meaning
- Improve clarity and professionalism
- Use Title Case
- Output ONLY a valid JSON array of strings
"""

    title_response = llm.invoke([HumanMessage(content=title_prompt)])

    try:
        title_options = json.loads(title_response.content.strip())
        title_options = [str(t) for t in title_options][:6]
    except Exception:
        title_options = []

    if title_options:
        title_options.append("None of the above (keep current title)")
        questions.append({
            "question": "Please select the most appropriate job title, if you would like to redefine it.",
            "options": title_options
        })

    # =====================================================
    # 2️⃣ EXCEL + DRAFT JD GAP ANALYSIS (KEY CHANGE)
    # =====================================================
    dynamic_prompt = f"""
You are a senior HR professional.

Your goal is to ensure the final Job Description
is accurate, complete, and non-misleading.

You are given TWO sources of truth:

SOURCE 1: EXCEL / INTAKE DATA
{form_context}

SOURCE 2: DRAFT JOB DESCRIPTION
{draft_jd if draft_jd.strip() else "No draft JD provided yet."}

While reviewing, identify:
- Information present in Excel but missing in the JD
- Information stated in the JD but not supported by Excel
- Areas where the JD makes assumptions
- Sections where clarity is insufficient or misleading

Ask clarifying questions ONLY for those issues.

TASK:
Analyze the Excel data and the draft JD together.

Identify ONLY those aspects of THIS ROLE that:
- Are unclear
- Are missing
- Are assumed without evidence
- Could be misunderstood by a candidate

Ask clarifying questions ONLY for those aspects.

IMPORTANT:
- Different roles must result in different questions
- Do NOT attempt to cover all JD areas
- Do NOT ask a question unless this specific role truly needs it


STRICT RULES:
- Do NOT invent responsibilities
- Do NOT assume technical, repair, inventory, or product duties
  unless explicitly stated in either source
- Do NOT repeat clearly aligned information
- If a question only improves wording, do NOT ask it
- Ensure at least ONE question clarifies role boundaries
- Cover at least 5 different JD sections
- Ask no more than ONE question per JD section

QUESTION RULES:
- 6-7 questions maximum
- Multiple-choice only (3–4 realistic options)
- Neutral wording (no seniority or skill assumptions)
- Each question must materially change JD accuracy

OUTPUT:
Return ONLY valid JSON.
No explanations. No extra text.

FORMAT:
[
  {{
    "question": "string",
    "options": ["string", "string", "string"]
  }}
]
"""

    response = llm.invoke([HumanMessage(content=dynamic_prompt)])

    try:
        parsed = json.loads(response.content.strip())
    except Exception:
        parsed = []

    # =====================================================
    # 3️⃣ QUALITY FILTER (UNCHANGED, STILL IMPORTANT)
    # =====================================================
    banned_keywords = [
        "repair", "spare", "inventory", "fix rate",
        "certification", "expert level", "years of experience"
    ]

    def is_high_quality_question(q):
        text = q["question"].lower()
        return not any(b in text for b in banned_keywords)

    if isinstance(parsed, list):
        for q in parsed:
            if (
                isinstance(q, dict)
                and isinstance(q.get("question"), str)
                and isinstance(q.get("options"), list)
                and 3 <= len(q["options"]) <= 4
                and is_high_quality_question(q)
            ):
                questions.append(q)

    return questions





