from langchain_core.messages import HumanMessage
import json


def generate_role_specific_clarifying_questions(llm, row):
    """
    Generates high-quality clarifying questions for JD creation.
    - First question: job title refinement
    - Remaining questions: derived ONLY from JD gaps discovered
      while attempting to draft the JD.
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
    # Raw form context (no interpretation)
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
    # 2️⃣ JD GAP–DRIVEN CLARIFYING QUESTIONS (ENHANCED)
    # =====================================================
    dynamic_prompt = f"""
You are a senior HR professional.

Your task is NOT to guess the role.
Your task is to produce a clear, accurate,
and non-misleading Job Description.

JOB TITLE:
{job_title}

RAW FORM DATA:
{form_context}

TASK:
First, internally attempt to draft a Job Description
using ONLY the information provided.

While drafting, identify where assumptions would be required,
where clarity is missing, or where the JD could become misleading.

Ask clarifying questions ONLY for those points.

JD SECTIONS TO CONSIDER:
- Core responsibilities
- Day-to-day activities
- Scope boundaries (what the role does NOT include)
- Success metrics / performance expectations
- Work environment (office / field / hybrid)
- Travel or shift expectations
- Tools or systems used
- Reporting & collaboration

MANDATORY RULES:
- Do NOT assume technical, repair, inventory, product, or execution duties
  unless explicitly stated in the form data
- Do NOT narrow or expand the role incorrectly
- Do NOT repeat information already provided
- If answering a question only changes wording, do NOT ask it
- Ensure at least ONE question clarifies role boundaries (out-of-scope work)
- Cover at least 5 different JD sections
- Ask no more than ONE question per JD section

QUESTION RULES:
- 6–8 questions maximum
- Each question must be multiple-choice (3–4 realistic options)
- Neutral, non-assumptive wording
- Each question must materially affect JD content

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
    # 3️⃣ QUALITY FILTER (HARD GUARD)
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
