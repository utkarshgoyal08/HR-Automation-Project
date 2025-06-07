import streamlit as st
import pandas as pd
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline
from pypdf import PdfReader
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import uuid
import re
import io

st.set_page_config(page_title="HR Automation Portal - Application", layout="wide")

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open_by_key("1ELd_iiUv_QW5iqhrFdDeloXRvtOwEOdvwxbJc1pa7YI")

try:
    jd_worksheet = SHEET.worksheet("Job_Description")
except gspread.exceptions.WorksheetNotFound:
    jd_worksheet = SHEET.add_worksheet(title="Job_Description", rows=1, cols=1)
    jd_worksheet.update_cell(1, 1, """
**Data Analyst Intern Job Description**

We are seeking a motivated Data Analyst Intern to join our team. The ideal candidate will assist in analyzing complex datasets to provide actionable insights, support data-driven decision-making, and contribute to ongoing projects.

**Key Responsibilities:**
- Collect, clean, and analyze large datasets using Python, R, or SQL.
- Create visualizations and dashboards using tools like Tableau, Power BI, or Matplotlib.
- Assist in developing predictive models and statistical analyses.
- Collaborate with cross-functional teams to identify trends and patterns.
- Document findings and present results to stakeholders.

**Requirements:**
- Pursuing a degree in Data Science, Statistics, Computer Science, or related field.
- Proficiency in Python (Pandas, NumPy) and/or R.
- Familiarity with SQL and database management.
- Experience with data visualization tools (e.g., Tableau, Power BI).
- Knowledge of machine learning basics is a plus.
- Strong problem-solving skills and attention to detail.
- Prior projects involving data analysis or machine learning are highly desirable.
""")
JOB_DESCRIPTION = jd_worksheet.get('A1')[0][0]

# Initialize Google Drive API
DRIVE_SERVICE = build('drive', 'v3', credentials=CREDS)

# Initialize Hugging Face models for scoring
technical_scorer = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
match_scorer = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
project_scorer = pipeline("text-classification", model="distilbert-base-uncased")

def extract_resume_text(uploaded_file):
    """Extract text from uploaded PDF resume."""
    if uploaded_file is not None:
        pdf = PdfReader(uploaded_file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text
    return ""

def clean_text(text):
    """Clean extracted resume text."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def score_technical_skills(resume_text):
    """Score technical skills using DistilBERT."""
    keywords = ["Python", "R", "SQL", "Tableau", "Power BI", "Pandas", "NumPy", "machine learning", "statistics"]
    score = 0
    for keyword in keywords:
        if keyword.lower() in resume_text.lower():
            score += 10
    result = technical_scorer(resume_text[:512])
    sentiment_score = result[0]['score'] if result[0]['label'] == 'POSITIVE' else 1 - result[0]['score']
    return min(score + (sentiment_score * 20), 100)

def score_job_match(resume_text, job_description):
    """Score job match using DistilBERT zero-shot classification."""
    labels = ["high match", "medium match", "low match"]
    input_text = f"Resume: {resume_text[:256]} Job Description: {job_description[:256]}"
    result = match_scorer(input_text, candidate_labels=labels, hypothesis_template="This resume is a {} for the job.")
    scores = result['scores']
    if result['labels'][0] == "high match":
        return scores[0] * 100
    elif result['labels'][0] == "medium match":
        return scores[0] * 60
    else:
        return scores[0] * 30

def score_projects(resume_text):
    """Score projects using DistilBERT."""
    project_keywords = ["project", "developed", "analyzed", "model", "dashboard", "visualization"]
    project_count = sum(resume_text.lower().count(keyword) for keyword in project_keywords)
    score = min(project_count * 10, 80)
    result = project_scorer(resume_text[:512])
    sentiment_score = result[0]['score'] if result[0]['label'] == 'POSITIVE' else 1 - result[0]['score']
    return min(score + (sentiment_score * 20), 100)

def upload_pdf_to_drive(file, filename):
    """Upload PDF to Google Drive and return the file's web view link."""
    file_metadata = {
        'name': filename,
        'mimeType': 'application/pdf'
    }
    media = MediaIoBaseUpload(file, mimetype='application/pdf')
    file = DRIVE_SERVICE.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    DRIVE_SERVICE.permissions().create(
        fileId=file.get('id'),
        body={
            'type': 'user',
            'role': 'reader',
            'emailAddress': 'your-email@example.com'  # Replace with your actual Google account email
        }
    ).execute()
    return file.get('webViewLink')

def save_to_google_sheets(data, pdf_link):
    """Save candidate data, scores, and PDF link to Google Sheets."""
    worksheet = SHEET.worksheet("sheet1")
    worksheet.append_row([
        data['candidate_id'],
        data['Name'],
        data['Phone'],
        data['Email'],
        data['LinkedIn'],
        data['technical_score'],
        data['match_score'],
        data['project_score'],
        pdf_link
    ])

st.title("HR Automation Portal - Data Analyst Intern Application")

st.header("Navigation")
col1, col2 = st.columns(2)
with col1:
    try:
        if st.button("Go to HR Portal"):
            st.switch_page("pages/HR_Portal.py")
    except st.errors.StreamlitAPIException:
        st.error("Could not find HR Portal. Please ensure 'HR_Portal.py' is in the 'pages' directory.")
        st.markdown("[Go to HR Portal](/HR_Portal)")
with col2:
    if st.button("Return to Home"):
        st.switch_page("app.py")

st.markdown(JOB_DESCRIPTION)

st.header("Candidate Application Form")
with st.form(key="application_form"):
    name = st.text_input("Full Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email Address")
    linkedin = st.text_input("LinkedIn Profile URL")
    resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    submit_button = st.form_submit_button("Submit Application")

if submit_button:
    if name and phone and email and resume:
        resume_text = extract_resume_text(resume)
        cleaned_resume = clean_text(resume_text)
        
        candidate_id = str(uuid.uuid4())
        
        resume.seek(0)
        pdf_filename = f"Resume_{candidate_id}.pdf"
        pdf_link = upload_pdf_to_drive(resume, pdf_filename)
        
        technical_score = score_technical_skills(cleaned_resume)
        match_score = score_job_match(cleaned_resume, JOB_DESCRIPTION)
        project_score = score_projects(cleaned_resume)
        
        candidate_data = {
            'candidate_id': candidate_id,
            'Name': name,
            'Phone': phone,
            'Email': email,
            'LinkedIn': linkedin,
            'technical_score': technical_score,
            'match_score': match_score,
            'project_score': project_score
        }
        save_to_google_sheets(candidate_data, pdf_link)
        
        st.success("Thank you for applying! Your application has been submitted successfully.")
    else:
        st.error("Please fill out all fields and upload a resume.")