import streamlit as st
import pandas as pd
import requests

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("fitness_users_dataset_final.csv")

df = load_data()

# Set your Groq API endpoint and API key securely
groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
groq_api_key = st.secrets["groq"]["api_key"]

def query_groq_llama(prompt):
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant who analyzes fitness customer datasets and answers questions."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(groq_api_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        st.error(f"Error occurred: {response.status_code} - {response.text}")
        return None

def main():
    st.title("Fitness Customer Insights Assistant")
    st.write("Ask anything about a customer's profile or get trends from the dataset.")

    st.subheader("Sample Data Preview")
    st.dataframe(df.head(3))

    query = st.text_input("Enter your question (e.g., 'Tell me about Sarah Brown', 'What are the top goals by gender?')")

    if st.button("Submit"):
        if query:
            st.write(f"Your query: **{query}**")

            # Convert dataset to CSV format for LLM context
            dataset_context = df.to_csv(index=False)

            prompt = f"""
You are a helpful assistant who provides answers to fitness-related questions by analyzing customer data.

Here is the dataset in CSV format:
{dataset_context}

User question: {query}

Provide a detailed, accurate, and helpful answer. Mention specific customer insights if a name is provided. Do not include or generate any Python code.
"""

            answer = query_groq_llama(prompt)

            if answer:
                st.subheader("Insightful Answer")
                st.write(answer)

if __name__ == "__main__":
    main()
