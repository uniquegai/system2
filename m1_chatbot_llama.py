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
    return pd.read_csv("m1_data.csv")

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
    st.title("M1 Dynamic Data Bot")
    st.write("Interact with your M1 data dynamically!")

    # Initialize session state to store conversation
    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    # Show dataset preview
    st.subheader("Dataset Preview")
    st.dataframe(df.head(3))  # Display the first 5 rows

    # User Input
    query = st.text_input("What insights are you seeking? (e.g., What’s the total value of orders in 2024?)")

    if st.button("Submit"):
        if query:
            st.write(f"Your query: **{query}**")

            # Store the user's query in the conversation history
            st.session_state.conversation.append({"role": "user", "content": query})

            # Use Groq LLaMA to generate Python code based on the user query
            groq_prompt = f"""
            You are a helpful assistant that generates Python code for data analysis. The dataset contains the following columns:
            {', '.join(df.columns)}

            Remove records with empty rows.
            If a column uses the `to_period()` function (e.g., for months or quarters), ensure that `NaT` values are removed first before applying `.to_period()`.
            Ensure that numerical values are properly formatted before concatenation to avoid type errors. When storing the result in `output_data`, use formatted string literals to format numerical values properly. 
            example:output_data = f"Average Order Value: (avg_order_value:.2f), Average Cashback: (avg_cashback:.2f)".This ensures that numerical values are converted to strings with two decimal places before being concatenated.
            Ensure that the numerical columns, such as 'Estimate Optimise Cashback Value' and 'Estimate Order Value', are properly converted before processing.  
                1. First, check if they are strings before applying `.str.replace()`.  
                2. If they are not strings, convert them using `.astype(str)`.  
                3. After removing commas using `.str.replace(',', '')`, convert them to numeric using `pd.to_numeric(..., errors='coerce')`.  

            Please ensure that the 'Advertiser' and 'Status' columns are cleaned by replacing specific values as follows if user query asks about advertiser or status, if needed:

            1. **For the 'Advertiser' column**:
                - 'Samsung Singapore' -> 'Samsung SG'
                - 'Lazada (SG)' -> 'Lazada SG'
                - 'Fairprice ON' -> 'FairPrice Online'
                - 'Shopee Singapore' -> 'Shopee Singapore'
                - 'Shopee SG - CPS' -> 'Shopee Singapore'
                - 'tripcom' -> 'Trip.com'
                - 'Decathlon' -> 'Decathlon SG'
                - 'Nike (APAC)' -> 'Nike APAC'
                - 'Klook' -> 'Klook Travel (CPS)'
                - 'Watsons Singapore' -> 'Watsons SG'
                - 'Charles & Keith (SG) CPS' -> 'Charles & Keith'
                - 'Klook Travel - CPS' -> 'Klook'
                - 'Klook Travel (CPS)' -> 'Klook'
                - 'Puma Singapore' -> 'Puma'

            2. **For the 'Status' column**:
                - 'APR' -> 'Approved'
                - 'pending' -> 'Pending'
                - 'rejected' -> 'Rejected'

            Replace the values in the 'Advertiser' and 'Status' column as per the above mappings if needed.

            The relevant columns for specific terms are as follows:
            - "cashback", "total cashback", or similar terms refer to "Estimate Optimise Cashback Value".
            - "order amount", "total order amount", or similar terms refer to "Estimate Order Value".
            
            Status column represent the status of the cashback.

            The 'Conversion Time' column uses the format `dd/mm/yyyy hh:mm`. 
            If any sequence or column used for aggregation (such as `idxmax()`, `max()`, or other similar operations) is empty or contains NaT, please ensure that the code properly handles these cases by checking if the sequence is empty before applying operations like `idxmax()`, `max()`, or any other operation that assumes non-empty data. If the sequence is empty, use a fallback value like `None`, `0`, or any suitable default value to prevent errors.
            Please ensure that the 'Conversion Time' column is parsed with the correct format (`%d/%m/%Y %H:%M`), and handle any errors during the parsing process by using the `errors='coerce'` option so that any invalid date values are converted to `NaT`.
            If a column uses the to_period() function (e.g., for months), ensure that the result is converted to a string using .dt.strftime('%Y-%m') for month-based periods, or .astype(str) for other cases. This prevents serialization errors when plotting with Plotly or processing JSON data.
            The user has requested the following:
            {query}

            Generate Python code that can process this request and provide the answer.
            The Python code should use the pandas library to process the dataset. If the query involves generating a graph or plot, use Plotly for visualization,
            and ensure to display the plot using st.plotly_chart(fig) for integration with a Streamlit app instead of using fig.show().
            Return only the Python code, no explanations or extra text.
            Please generate Python code that can process this request and provide the answer. Do **not include** any markdown or code block formatting (` ```python` or ` ``` `). Just give the Python code directly.
            my dataset file name is: m1_data.csv
            when generating Python code, ensure the result is displayed first using Streamlit functions (`st.write()`, `st.dataframe()`, etc.). Once the result is displayed, store it in the variable 'output_data' in the last line of the code. Ensure that the result is properly displayed **before** being assigned to the 'output_data' variable.
            If the result is not a graph or fig, ensure that `output_data` stores the result incluing both the description and the calculated result.
            Only if the result is a graph or plot, do not include any descriptive text in `output_data`.
            
            """

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
                        You are a data analyst working on business insights for M1 based in Singapore in a meaningful manner.
                        M1 partners with a set of merchants to offer cashback promotions to its customers. These offers are designed to increase engagement and encourage more transactions and to satisfied the customer with the M1 business.

                    
                        Analyze the following graph:
                        {exec_globals.get('fig')}
                        Provide insights focusing on:
                        - Any significant trends, low/high points, and potential implications.
                        - Key observations and their impact on business decision-making.

                        **Do not provide any Python code after explanation**
                        """

                    else:
                        # Handle other output types (DataFrame, list, dict, or generic text)
                        output_data = exec_globals.get('output_data', None)

                        # Generate explanation prompt without displaying the data in Streamlit
                        explanation_prompt = f"""
                        You are a data analyst working on business insights for M1 based in Singapore in a meaningful manner.
                        M1 partners with a set of merchants to offer cashback promotions to its customers. These offers are designed to increase engagement and encourage more transactions and to satisfied the customer with the M1 business.

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
