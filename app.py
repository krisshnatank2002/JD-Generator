import streamlit as st
import os

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
# UI
# ==========================================
st.title("🧠 AI Job Description Generator")
st.caption("Generate professional JDs directly from Google Form data")
st.divider()

# ==========================================
# 🔑 HELPER: FIND JOB TITLE COLUMN
# ==========================================
def find_job_title_column(df):
    for col in df.columns:
        if "job" in col.lower() and "title" in col.lower():
            return col
    return None

# ==========================================
# LOAD GOOGLE FORM DATA
# ==========================================
if st.button("📥 Fetch Latest Google Form Responses"):
    df = load_form_data()

    job_title_col = find_job_title_column(df)

    if not job_title_col:
        st.error("❌ Job Title column not found in Google Sheet")
        st.write("Available columns:", list(df.columns))
        st.stop()

    # Label only for dropdown
    df["JD_Label"] = df[job_title_col].fillna("Untitled Role")

    st.session_state["data"] = df
    st.session_state["job_title_col"] = job_title_col

    st.success(f"✅ {len(df)} responses loaded")
    st.dataframe(df.head())

st.divider()

# ==========================================
# HELPER: RADIO WITH NONE OPTION
# ==========================================
def radio_with_none(question, options, key):
    final_options = options + ["None of the above"]
    selected = st.radio(question, final_options, key=key)
    return "Not Applicable" if selected == "None of the above" else selected

# ==========================================
# JD FLOW
# ==========================================
if "data" in st.session_state:

    df = st.session_state["data"]
    job_title_col = st.session_state["job_title_col"]

    selected_jd = st.selectbox(
        "🎯 Select Job Title",
        df["JD_Label"].tolist()
    )

    # ================================
    # STEP 1: GENERATE DRAFT JD
    # ================================
    if st.button("🚀 Generate Draft JD"):

        selected_row = df[df["JD_Label"] == selected_jd].iloc[0].copy()

        # Persist original job title
        selected_row["__job_title__"] = selected_row[job_title_col]

        st.session_state["selected_row"] = selected_row

        with st.spinner("Generating draft JD..."):
            st.session_state["draft_jd"] = generate_ranked_jd(selected_row)

        with st.spinner("Generating clarifying questions..."):
            # ✅ FIXED: pass ROW only
            st.session_state["questions"] = generate_role_specific_clarifying_questions(
                llm,
                selected_row
            )

        st.session_state["answers"] = {}
        st.success("✅ Draft JD & clarifying questions ready")

    # ================================
    # STEP 2: SHOW QUESTIONS
    # ================================
    if "questions" in st.session_state:

        st.markdown("### 🔍 Clarify Role Requirements")

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

        row = st.session_state["selected_row"].copy()

        if "__job_title__" not in row:
            row["__job_title__"] = row[job_title_col]

        with st.spinner("Generating FINAL JD..."):
            final_jd = generate_ranked_jd(
                row,
                clarifications=st.session_state.get("answers", {})
            )

            doc = write_jd_to_docx(final_jd, row)

            os.makedirs("output", exist_ok=True)
            safe_title = row[job_title_col].replace("/", "_")
            path = f"output/{safe_title}.docx"
            doc.save(path)

        st.success("🎉 Final JD generated")

        with open(path, "rb") as f:
            st.download_button(
                "⬇️ Download JD",
                f,
                file_name=f"{safe_title}.docx"
            )

else:
    st.info("ℹ️ Load Google Form data first")
