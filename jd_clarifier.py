from langchain_core.messages import HumanMessage
import json


def generate_role_specific_clarifying_questions(llm, row):
    """
    Generate clarifying questions based on Google Form / Excel data,
    NOT on draft JD.
    """

    # ----------------------------
    # Resolve Job Title safely
    # ----------------------------
    job_title = "This role"
    for k in row.index:
        if "job" in k.lower() and "title" in k.lower():
            job_title = str(row[k]).strip()
            break

    core_responsibility = row.get(
        "What is the single core responsibility of this role?", ""
    )

    experience = row.get("Minimum experience required", "")
    education = row.get("Minimum education required", "")
    work_mode = row.get("Work mode", "")
    travel = row.get("Does this role require travel?", "")
    urgency = row.get("How urgent is this hire?", "")

    prompt = f"""
You are an HR consultant.

ROLE CONTEXT (FROM FORM DATA):
Job Title: {job_title}
Core Responsibility: {core_responsibility}
Experience Required: {experience}
Education Required: {education}
Work Mode: {work_mode}
Travel Requirement: {travel}
Hiring Urgency: {urgency}

TASK:
Generate 6–8 clarifying questions a hiring manager should answer
to finalize this role.

RULES:
- Questions must be strictly relevant to THIS job title
- Do NOT assume a technical role unless the title clearly says so
- Questions should refine:
  - scope
  - targets / KPIs
  - seniority
  - responsibilities
  - expectations
- Each question must be multiple-choice (3–4 options)
- Output ONLY valid JSON in this exact format:

[
  {{
    "question": "string",
    "options": ["string", "string", "string"]
  }}
]

DO NOT include explanations.
DO NOT include any text outside JSON.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    # ----------------------------
    # Safe JSON parsing
    # ----------------------------
    try:
        parsed = json.loads(raw)
    except Exception:
        return []

    # ----------------------------
    # Validate structure
    # ----------------------------
    valid_questions = []

    if isinstance(parsed, list):
        for q in parsed:
            if (
                isinstance(q, dict)
                and isinstance(q.get("question"), str)
                and isinstance(q.get("options"), list)
                and len(q["options"]) >= 2
            ):
                valid_questions.append(q)

    return valid_questions
