from langchain_core.messages import HumanMessage
import json


def generate_role_specific_clarifying_questions(llm, row):
    """
    FIRST question: fixed (job title refinement)
    Remaining questions: completely LLM-decided, role-specific,
    based ONLY on what improves the JD and what is missing.
    """

    # ----------------------------
    # Resolve Job Title
    # ----------------------------
    job_title = "This role"
    for k in row.index:
        if "job" in k.lower() and "title" in k.lower():
            job_title = str(row[k]).strip()
            break

    # Pass ALL form data as raw context (no interpretation)
    form_context = "\n".join(
        f"{k}: {row[k]}" for k in row.index if str(row[k]).strip()
    )

    questions = []

    # =====================================================
    # 1️⃣ FIXED FIRST QUESTION — JOB TITLE REFINEMENT
    # =====================================================
    title_prompt = f"""
You are an HR expert.

Current job title:
"{job_title}"

Generate 5–6 professional alternative job titles
that are suitable for hiring and job postings.

Rules:
- Keep the same role meaning
- Improve clarity and professionalism
- Use Title Case
- Output ONLY valid JSON array of strings
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
            "question": "Is this the most suitable and professional job title for this role?",
            "options": title_options
        })

    # =====================================================
    # 2️⃣ FULLY DYNAMIC JD-ENHANCING QUESTIONS (NO TEMPLATE)
    # =====================================================
    dynamic_prompt = f"""
You are a senior hiring manager and HR expert.

Below is RAW DATA collected from a hiring intake form.
Some information may be incomplete, vague, or missing.

JOB TITLE:
{job_title}

FORM DATA:
{form_context}

TASK:
Decide on your own which clarifying questions MUST be asked
to significantly improve the final Job Description for this role.

IMPORTANT RULES:
- DO NOT follow any fixed structure or template
- DO NOT ask generic or repetitive questions
- DO NOT ask questions already clearly answered in the data
- Ask ONLY what is missing, unclear, or critical for this specific role
- Questions must differ depending on the job role
- Think like a hiring manager trying to avoid a weak or misleading JD
- Each question must be multiple-choice (3–4 realistic options)

OUTPUT REQUIREMENTS:
- Generate 7–8 questions
- Output ONLY valid JSON in the format below
- Do NOT include explanations or extra text

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
                and len(q["options"]) >= 2
            ):
                questions.append(q)

    return questions
