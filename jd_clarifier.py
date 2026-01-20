def generate_role_specific_clarifying_questions(llm, row):
    """
    Generate clarifying questions based on Google Form / Excel data,
    NOT on draft JD.
    """

    job_title = ""
    for k in row.index:
        if "job" in k.lower() and "title" in k.lower():
            job_title = row[k]
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
  • scope
  • targets / KPIs
  • seniority
  • responsibilities
  • expectations
- Each question must be multiple-choice (3–4 options)
- Output STRICTLY in this JSON-like format:

[
  {{
    "question": "...",
    "options": ["...", "...", "..."]
  }}
]

DO NOT mention software engineering unless role is technical.
DO NOT include explanations.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content.strip()

    try:
        parsed = eval(text)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []
