# jd_clarifier.py

from langchain_core.messages import HumanMessage


# =====================================================
# JOB TITLE CLARIFICATION (DYNAMIC)
# =====================================================
def generate_job_title_clarification(llm, job_title: str):
    prompt = f"""
You are an HR expert.

The given job title is:
"{job_title}"

Generate 5 professional, industry-standard alternative job titles.

Rules:
- Keep meaning the same
- Improve professionalism
- Vary wording slightly
- Use Title Case
- Output ONLY a comma-separated list
"""

    response = llm.invoke(prompt)
    titles = [t.strip() for t in response.content.split(",") if t.strip()]

    if len(titles) < 3:
        return None

    return {
        "question": "Would you like to redefine the job title for better professionalism?",
        "options": titles[:5]
    }


# =====================================================
# ROLE-SPECIFIC CLARIFYING QUESTIONS
# =====================================================
def generate_role_specific_clarifying_questions(
    llm,
    job_title: str,
    jd_text: str
):
    """
    Uses LLM to generate role-specific clarifying questions.
    Returns structured questions with MCQ options.
    """

    questions = []

    # 🔹 Job title clarification FIRST
    title_q = generate_job_title_clarification(llm, job_title)
    if title_q:
        questions.append(title_q)

    prompt = f"""
You are a senior HR consultant.

Job Title: {job_title}

Draft Job Description:
{jd_text}

Your task:
Generate 7-8 HIGHLY PRACTICAL clarification questions
that a hiring manager would answer to refine this role.

Rules:
- Questions must be multiple-choice
- Each question should have 3–4 realistic options

- Output STRICTLY in this JSON-like format:

[
  {{
    "question": "...",
    "options": ["...", "...", "..."]
  }}
]

DO NOT add any explanations or extra text.
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content.strip()

    try:
        parsed = eval(text)
        if isinstance(parsed, list):
            questions.extend(parsed)
    except Exception:
        pass

    return questions

