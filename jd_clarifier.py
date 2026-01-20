from langchain_core.messages import HumanMessage
import json


def generate_role_specific_clarifying_questions(llm, row):
    """
    FIRST question: fixed (job title refinement)
    Remaining questions: generated ONLY to fill JD gaps
    (scope, responsibilities, success criteria, environment).
    No role guessing, no technical assumptions.
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
            "question": "Select the most appropriate job title, if you wish to redefine the current title!",
            "options": title_options
        })

    # =====================================================
    # 2️⃣ JD GAP–DRIVEN CLARIFYING QUESTIONS (CORE FIX)
    # =====================================================
    dynamic_prompt = f"""
You are an expert HR professional.

Your ONLY goal is to write a clear, accurate,
and non-misleading Job Description.

You are given partial intake data.

JOB TITLE:
{job_title}

RAW FORM DATA:
{form_context}

TASK:
If you had to write the Job Description now,
identify which JD sections would be weak, unclear,
or misleading due to missing information.

For EACH such gap, ask ONE clarifying question.

JD SECTIONS YOU MAY CONSIDER:
- Core responsibilities
- Day-to-day activities
- Scope boundaries (what the role does NOT do)
- Success metrics / performance expectations
- Work environment (office / field / hybrid)
- Travel or shift expectations
- Tools or systems used
- Collaboration & reporting

STRICT RULES:
- DO NOT assume technical, repair, inventory, or product responsibilities
  unless they are explicitly mentioned in the form data
- DO NOT expand the role beyond the provided information
- DO NOT ask questions that narrow the role incorrectly
- DO NOT repeat information already present
- Ask ONLY questions that materially improve the JD

QUESTION RULES:
- 6–8 questions maximum
- Each question must be multiple-choice (3–4 realistic options)
- Neutral wording (no implied seniority or skill level)
- Each question must affect JD content meaningfully

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

    if isinstance(parsed, list):
        for q in parsed:
            if (
                isinstance(q, dict)
                and isinstance(q.get("question"), str)
                and isinstance(q.get("options"), list)
                and 3 <= len(q["options"]) <= 4
            ):
                questions.append(q)

    return questions

