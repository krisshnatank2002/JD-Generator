import streamlit as st
import os
import base64

from google_sheets import load_form_data
from jd_generator import generate_ranked_jd, write_jd_to_docx
from jd_clarifier import generate_role_specific_clarifying_questions
from langchain_groq import ChatGroq

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="AI Job Description Generator",
    layout="centered"
)

# ==========================================
# ENV CHECK (FAIL FAST)
# ==========================================
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ GROQ_API_KEY not found in Streamlit Secrets")
    st.stop()

# ==========================================
# INIT LLM
# ==========================================
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# ==========================================
# STEP 1: DARK UI THEME (FIXED)
# ==========================================
st.markdown(
    """
    <style>
    /* APP BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #0b0f1a 0%, #0e1424 100%);
        color: #ffffff;
    }

    /* HEADINGS */
    h1 {
        font-size: 3rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.25rem;
    }

    h2, h3, h4 {
        color: #e5e7eb;
        font-weight: 700;
    }

    p, span, label {
        color: #d1d5db !important;
        font-size: 15px;
    }

    /* DIVIDER */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #374151, transparent);
        margin: 2rem 0;
    }

    /* RADIO CARD */
    div[data-testid="stRadio"] {
        background: rgba(17, 24, 39, 0.85);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }

    /* RADIO LABELS */
    div[data-testid="stRadio"] label {
        color: #e5e7eb !important;
        font-size: 15px;
        line-height: 1.6;
    }

    /* RADIO BUTTON */
    div[data-testid="stRadio"] input[type="radio"] {
        accent-color: #22c55e;
        transform: scale(1.15);
        margin-right: 10px;
    }

    /* BUTTONS */
    .stButton > button {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: #ffffff;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-size: 16px;
        font-weight: 700;
        border: none;
        box-shadow: 0 8px 20px rgba(34, 197, 94, 0.35);
        transition: all 0.2s ease-in-out;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 28px rgba(34, 197, 94, 0.45);
    }

    /* SELECT BOX */
    div[data-testid="stSelectbox"] {
        background: rgba(17, 24, 39, 0.85);
        border-radius: 12px;
        padding: 6px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* DATAFRAME */
    .stDataFrame {
        background: rgba(17, 24, 39, 0.9);
        border-radius: 12px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# UI HEADER
# ==========================================
st.title("🧠 AI Job Description Generator")
st.caption("Generate professional JDs directly from Google Form data")
st.divider()

# ==========================================
# LOAD GOOGLE FORM DATA
# ==========================================
if st.button("📥 Fetch Latest Google Form Responses"):
    df = load_form_data()
    df["JD_Label"] = df["Job Title"].fillna("Untitled Role")
    st.session_state["data"] = df
    st.success(f"✅ {len(df)} responses loaded")
    st.dataframe(df.head())

st.divider()

# ==========================================
# HELPER: MCQ WITH 4TH OPTION
# ==========================================
def radio_with_none(question, options, key):
    final_options = options + ["None of the above"]

    selected = st.radio(
        question,
        final_options,
        key=key
    )

    if selected == "None of the above":
        return "Not Applicable"

    return selected

# ==========================================
# JD FLOW
# ==========================================
if "data" in st.session_state:

    df = st.session_state["data"]

    selected_jd = st.selectbox(
        "🎯 Select Job Title",
        df["JD_Label"].tolist()
    )

    # ================================
    # STEP 1: GENERATE DRAFT JD
    # ================================
    if st.button("🚀 Generate Draft JD"):
        selected_row = df[df["JD_Label"] == selected_jd].iloc[0]

        with st.spinner("Generating draft JD..."):
            st.session_state["selected_row"] = selected_row
            st.session_state["draft_jd"] = generate_ranked_jd(selected_row)

        with st.spinner("Generating clarifying questions..."):
            st.session_state["questions"] = (
                generate_role_specific_clarifying_questions(
                    llm,
                    selected_row.get("Job Title", ""),
                    st.session_state["draft_jd"]
                )
            )

        st.session_state["answers"] = {}
        st.success("✅ Draft JD & questions ready")

    # ================================
    # STEP 2: SHOW QUESTIONS (UI FIX)
    # ================================
    if "questions" in st.session_state:

        st.markdown("### 🔍 Clarify Role Requirements")
        st.markdown(
            "<p style='color:#9ca3af;'>Choose the most appropriate option. "
            "If unsure, select <b>None of the above</b>.</p>",
            unsafe_allow_html=True
        )

        for idx, q in enumerate(st.session_state["questions"]):
            st.session_state["answers"][q["question"]] = radio_with_none(
                question=q["question"],
                options=q["options"],
                key=f"clarify_{idx}"
            )

        # ================================
        # STEP 3: FINAL JD
        # ================================
        if st.button("✨ Generate FINAL Job Description"):

            with st.spinner("Generating FINAL JD..."):
                final_jd = generate_ranked_jd(
                    st.session_state["selected_row"],
                    clarifications=st.session_state["answers"]
                )

                doc = write_jd_to_docx(
                    final_jd,
                    st.session_state["selected_row"]
                )

                os.makedirs("output", exist_ok=True)
                job_title = (
                    st.session_state["selected_row"]
                    .get("Job Title", "JD")
                    .replace("/", "_")
                )
                path = f"output/{job_title}.docx"
                doc.save(path)

            st.success("🎉 Final JD generated")

            with open(path, "rb") as f:
                st.download_button(
                    "⬇️ Download JD",
                    f,
                    file_name=f"{job_title}.docx"
                )

else:
    st.info("ℹ️ Load Google Form data first")

