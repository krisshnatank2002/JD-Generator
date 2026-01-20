# jd_clarifier.py

from langchain_core.messages import HumanMessage

def generate_role_specific_clarifying_questions(
    llm,
    job_title: str,
    jd_text: str
):
    """
    Uses LLM to generate role-specific clarifying questions
    Returns structured questions with MCQ options
    """

    prompt = f"""
You are a senior HR consultant.

Job Title: {job_title}

Draft Job Description:
{jd_text}

Your task:
Generate 4–6 HIGHLY PRACTICAL clarification questions
that a hiring manager would answer to refine this role.

Rules:
- Questions must be multiple-choice
- Each question should have 3–4 realistic options
- Focus on scope, seniority, targets, tools, and expectations
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

    # Safe fallback parsing
    try:
        questions = eval(text)
        return questions if isinstance(questions, list) else []
    except Exception:
        return []
