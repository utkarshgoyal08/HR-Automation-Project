import streamlit as st

st.set_page_config(page_title="HR Automation Portal", layout="wide")

st.title("HR Automation Portal")
st.write("Welcome to the HR Automation Portal. Use the buttons below or the sidebar to navigate.")

col1, col2 = st.columns(2)
with col1:
    if st.button("Go to HR Portal"):
        st.switch_page("pages/HR_Portal.py")
with col2:
    if st.button("Go to Job Application Form"):
        st.switch_page("pages/Job_Application_Form.py")