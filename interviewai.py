import streamlit as st
import os
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import HuggingFaceEndpoint
import os

# Set your Hugging Face API key here or use environment variables
# Define the questions
questions = [
    "Tell us about yourself.",
    "Why are you interested in this position?",
    "Describe a challenging project you worked on.",
    "How do you handle tight deadlines?",
    "What makes you a good team player?",
    "Where do you see yourself in 3 years?",
]

# LLM setup using Hugging Face (FLAN-T5-XL)
llm = HuggingFaceHub(
    repo_id="google/flan-t5-xl",
    model_kwargs={"temperature": 0.2, "max_length": 100}
)

# Define Streamlit app UI
st.set_page_config(page_title="AI vs Human Answer Detector", page_icon="🤖")
st.title("🤖 AI vs Human Answer Detector")
st.write("Answer the questions below. The system will analyze if the responses are AI-written or human-typed.")

answers = []
for i, question in enumerate(questions):
    response = st.text_area(f"{i+1}. {question}", key=f"q{i}")
    answers.append(response)

def check_ai_generated(text):
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template="Decide if the following response is written by an AI or a human. Only respond with 'AI' or 'Human'.\n\nResponse: {text}"
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    result = chain.run(text)
    return result.strip()

if st.button("Submit Answers"):
    st.subheader("📊 Analysis Result")
    for i, answer in enumerate(answers):
        if answer.strip():
            verdict = check_ai_generated(answer)
            st.markdown(f"**Q{i+1}: {questions[i]}**")
            st.write(f"**Your Answer:** {answer}")
            st.write(f"🔍 **System Detected:** `{verdict}`\n")
        else:
            st.warning(f"No answer provided for Question {i+1}")
