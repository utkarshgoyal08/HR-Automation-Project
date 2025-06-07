import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Streamlit page configuration
st.set_page_config(page_title="HR Portal - Dashboard", layout="wide")

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open_by_key(os.getenv("GOOGLE_SHEET_ID"))

# Initialize Job Description worksheet
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

# Streamlit UI
st.title("HR Portal - Dashboard")

# Navigation buttons
st.header("Navigation")
col1, col2 = st.columns(2)
with col1:
    try:
        if st.button("Go to Job Application Form"):
            st.switch_page("pages/Job_Application_Form.py")
    except st.errors.StreamlitAPIException:
        st.error("Could not find Job Application Form. Please ensure 'Job_Application_Form.py' is in the 'pages' directory.")
        st.markdown("[Go to Job Application Form](/Job_Application_Form)")
with col2:
    if st.button("Return to Home"):
        st.switch_page("app.py")

# Job Description Management
st.header("Manage Job Description")
current_jd = jd_worksheet.get('A1')[0][0]
jd_input = st.text_area("Edit Job Description", value=current_jd, height=300)
if st.button("Update Job Description"):
    jd_worksheet.update_cell(1, 1, jd_input)
    st.success("Job description updated successfully!")

# Candidate Scores Visualization
st.header("Candidate Scores Distribution")
worksheet = SHEET.worksheet("sheet1")
data = worksheet.get_all_records()
if data:
    df = pd.DataFrame(data)
    if not df.empty:
        avg_technical = df['technical_score'].mean() if 'technical_score' in df else 0
        avg_match = df['match_score'].mean() if 'match_score' in df else 0
        avg_project = df['project_score'].mean() if 'project_score' in df else 0
        pie_data = pd.DataFrame({
            'Category': ['Technical Skills', 'Job Match', 'Projects'],
            'Average Score': [avg_technical, avg_match, avg_project]
        })
        fig = px.pie(pie_data, values='Average Score', names='Category', title='Average Candidate Scores')
        st.plotly_chart(fig)
    else:
        st.warning("No candidate data available for visualization.")
else:
    st.warning("No candidate data available for visualization.")

# Candidate Details
st.header("Candidate Details")
if st.button("Show Candidates"):
    if data:
        df = pd.DataFrame(data)
        print("Columns in sheet1:", df.columns.tolist())  # Debug: Print column names
        expected_columns = ['Name', 'Email', 'technical_score', 'match_score', 'project_score', 'Resume PDF Link']
        available_columns = [col for col in expected_columns if col in df.columns]
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing columns in Google Sheet: {', '.join(missing_columns)}. Please check sheet1 headers.")
        
        if available_columns:
            df_display = df[available_columns].copy()
            resume_column = 'Resume PDF Link' if 'Resume PDF Link' in df.columns else None
            if resume_column:
                df_display[resume_column] = df_display[resume_column].apply(lambda x: f'<a href="{x}" target="_blank">View Resume</a>')
            st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.error("No expected columns found in the Google Sheet. Please check sheet1 headers.")
    else:
        st.warning("No candidates found in the database.")
