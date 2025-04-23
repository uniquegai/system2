import streamlit as st
import pandas as pd
import plotly.express as px  # Plotly for graphing
import plotly.graph_objects as go
from PIL import Image
import io  # For capturing printed output
from contextlib import redirect_stdout  # Corrected import
# Ensure that kaleido is installed before using it
import plotly.graph_objects as go
import requests  # for Groq API interaction

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("fitness_users_dataset_final.csv")

df = load_data()


# Set your Groq API endpoint and API key securely
groq_api_url = "https://api.groq.com/openai/v1/chat/completions"  # Correct endpoint
groq_api_key = st.secrets["groq"]["api_key"]  # Make sure to securely fetch the API key from environment variables

def query_groq_llama(prompt):
    """
    Send a query to Groq LLaMA and get Python code as a response.
    """
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",  # Correct model name
        "messages": [
            {"role": "system", "content": "You are a helpful data assistant that generates Python code to process data."},
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
    # Streamlit app starts here
    st.title("Customer Search Bot")
    st.write("Look for customer details")

    # Initialize session state to store conversation
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    # Show dataset preview
    st.subheader("Dataset Preview")
    st.dataframe(df.head(3))  # Display the first 5 rows

    # User Input
    query = st.text_input("Ask the info you want to know about your customer?")

    if st.button("Submit"):
        if query:
            st.write(f"Your query: **{query}**")

            # Store the user's query in the conversation history
            st.session_state.conversation.append({"role": "user", "content": query})

            # Use Groq LLaMA to generate Python code based on the user query
            groq_prompt = f"""
            You are a helpful assistant that generates Python code for data analysis. The dataset contains the following columns:
            userid, address, assigned coach, assigned meal plan, birth date, physical problems, default meal plan, email, first name, last name, planid, product, phone number, coach notes about physical problems, daily activity level, days available to workout, current workout days, weight, user device, allergen tags, meal goals, gender, current weight, height, weight goal, dietary restrictions

            Remove records with empty rows.

            If a column uses the to_period() function (e.g., for months or quarters), ensure that NaT values are removed first before applying .to_period().

           Ensure that the numerical columns such as 'weight', 'height', and 'weight goal' are properly converted before processing:

            First, check if they are strings before applying .str.replace().

            If they are not strings, convert them using .astype(str).

            After removing commas using .str.replace(',', ''), convert them to numeric using pd.to_numeric(..., errors='coerce').

            The 'birth date' column should is in the format of "YYYY-MM-DD", and the age should be computed using today's date.

            The relevant columns for specific terms are as follows:
            "age", "birthdate" refer to "birth date"
            "goal", "fitness goal", or "what they want to achieve" refers to "meal goals"
            "meal plan" refers to "assigned meal plan"
            "health issue", "physical condition", or "fitness problem" refers to "physical problems"

            If any column used for aggregation (such as idxmax(), max(), or other similar operations) is empty or contains NaT, ensure that the code properly handles these cases by checking if the sequence is empty before applying such operations. If empty, use a fallback value like None, 0, or another default value to prevent errors.

            The user has requested the following:
            Show the customer name, age, gender, physical problem, meal plan, and fitness goal. Present it in a table format with brief user description.

            Generate Python code that can process this request and provide the answer.
            The Python code should use the pandas library to process the dataset.
            If the query involves generating a graph or plot, use Plotly for visualization, and ensure to display the plot using st.plotly_chart(fig) for Streamlit compatibility.

            Return only the Python code, no explanations or extra text.
            Please generate Python code that can process this request and provide the answer.
            Do not include any markdown or code block formatting ( ```python or ```). Just give the Python code directly.

            My dataset file name is: fitness_users_dataset_final.csv
            When generating Python code, ensure the result is displayed first using Streamlit functions (st.write(), st.dataframe(), etc.).
            Once the result is displayed, store it in the variable output_data in the last line of the code. Ensure that the result is properly displayed before being assigned to the output_data variable.
            If the result is not a graph or fig, ensure that output_data stores the result including both the description and the calculated result.
            Only if the result is a graph or plot, do not include any descriptive text in output_data."""

            python_code = query_groq_llama(groq_prompt)

            #st.write("Generated Python Code:")
            #st.code(python_code)

            if python_code:
                try:
                    # Define a dictionary for the code execution environment
                    exec_globals = {"df": df, "pd": pd, "px": px, "st": st}

                    # Execute the Python code in the given environment
                    exec(python_code, exec_globals)

                    # Check if the output is a Plotly figure
                    if isinstance(exec_globals.get('fig'), go.Figure):
                        # Generate explanation prompt for the graph
                        explanation_prompt = f"""
                        You are a data analyst working on personalized fitness insights for a US-based health and wellness platform. This platform partners with professional coaches and nutrition experts to provide meal plans and fitness programs that help customers achieve their health goals.

                        Analyze the following graph:
                        {exec_globals.get('fig')}

                        Provide insights focusing on:
                        Patterns and trends based on gender, age, fitness goals, or physical problems.
                        Any significant peaks or drops in activity, health issues, or goal preferences.
                        Key observations that could impact product design, coaching strategy, or personalized recommendations.
                        Consider how health conditions (e.g., knee pain, spine issues) might influence meal plans or activity levels.
                        Additionally, provide a short description about what the typical customer looks like based on the data:
                        Age and gender distribution
                        Most common health issues
                        Most popular fitness goals and meal plans
                        Any correlations between physical issues and their goals or meal strategies
                        Do not provide any Python code after explanation.
                        """

                    else:
                        # Handle other output types (DataFrame, list, dict, or generic text)
                        output_data = exec_globals.get('output_data', None)

                        # Generate explanation prompt without displaying the data in Streamlit
                        explanation_prompt = f"""
                        You are a data analyst working on fitness insights for Fitness coaches to provide insights in a meaningful manner for their customers.
                        System2 supports Fitness coaches to connect with their clients and provide necessary fintess recommendations faster and accurate 
                        
                        Analyze the following output:
                        {output_data}
                        Provide insights focusing on:
                        - Key observations and their significance.
                        - Any notable trends or patterns and their implications.

                        **Do not provide any Python code after explanation**
                        """

                    # Pass the explanation prompt to the LLM
                    explanation = query_groq_llama(explanation_prompt)

                    # Display only the explanation in Streamlit
                    st.write("Explanation:")
                    st.write(explanation)

                    # Store assistant's response in the conversation history
                    st.session_state.conversation.append({"role": "assistant", "content": explanation})

                    ## Now show results progressively
                    #if len(st.session_state.conversation) > 1:
                        ## Show first response first and second after that
                        #st.write("First Query Result:")
                        #st.write(st.session_state.conversation[0]["content"])

                        # Then show the second response (current one)
                        #st.write("Second Query Result:")
                        #st.write(explanation)

                except SyntaxError as e:
                    st.error("Oops! The generated code had a syntax issue. Please try again.")
                    st.error(f"Syntax Error in generated code: {e}")
                except Exception as e:
                    st.error("An unexpected error occurred. Please try again.")
                    st.error(f"An error occurred while executing the code: {e}")



# Run the app
if __name__ == "__main__":
    main()
