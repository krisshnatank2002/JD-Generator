import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os

def load_form_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=scopes
    )

    client = gspread.authorize(creds)

    SPREADSHEET_ID = "1SpNGsY707CaY6i06knI9F2HJdtAcHxGKq8IjAb17oWo"
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # ==========================================
    # CLEAN COLUMN NAMES
    # ==========================================
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    # ==========================================
    # RENAME GOOGLE FORM QUESTIONS → INTERNAL KEYS
    # ==========================================
    df = df.rename(columns={

        "Job Title ( Example: AI Engineer, Sales Executive, HR Manager)": "Job Title",
        "Location": "Location",
        "Employment Type ( Full-time / Contract / Internship )": "Role Type",
        "Work mode": "Work Mode",
        "Minimum experience required": "Experience",
        "Minimum education required": "Education",
        "Does this role require travel?": "Travel",
        "How urgent is this hire?": "Hiring Priority",
        "Is this role building something new or scaling an existing function?": "Role Context",
        "Reporting To (Example: Tech Lead, Sales Manager)": "Reporting To",
        "What is the single core responsibility of this role?": "Role Overview",
        "Key Responsibilities ( List 4–6 things this person will actually do)": "Responsibilities",
        "Growth opportunities in this role ( Promotion, learning, leadership, etc.)": "Growth",
        "What type of person will succeed in this role? (Work style, mindset, attitude)": "Ideal Candidate",
        "Top 3 skills this role MUST have": "Core Skills",
        "other skills ( Example: Python, Excel, Communication )": "Other Skills",
    })

    return df
