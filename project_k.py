import streamlit as st
from github import Github, UnknownObjectException
import re
import openai
# Set up your OpenAI API credentials
openai.api_key = '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'

# Authenticate with GitHub API using a personal access token
g = Github("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")

@st.cache
def fetch_code_from_repository(repository):
    # Get the repository object
    try:
        repo = g.get_repo(repository)
    except UnknownObjectException:
        return ""

    # Fetch the code from the default branch (e.g., main)
    contents = repo.get_contents("")

    # Initialize an empty string to store the code
    code = ""

    # Recursively traverse the repository's file structure to retrieve the code
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        elif file_content.type == "file":
            # Fetch the content of the file
            file_data = file_content.decoded_content.decode("utf-8")
            # Concatenate the code to the existing code string
            code += file_data

    return code

def preprocess_code(code):
    # Remove comments from the code
    code = remove_comments(code)

    # Remove blank lines from the code
    code = remove_blank_lines(code)

    # Remove trailing whitespaces
    code = remove_trailing_whitespaces(code)

    # Exclude specific file types if needed
    # You can add more file types to exclude
    excluded_file_types = ['.txt', '.csv']
    if any(file_type in code for file_type in excluded_file_types):
        return ""

    return code

def remove_comments(code):
    # Remove single-line comments
    code = re.sub(r"\/\/.*", "", code)
    
    # Remove multi-line comments
    code = re.sub(r"\/\*.*?\*\/", "", code, flags=re.DOTALL)

    return code

def remove_blank_lines(code):
    code_lines = code.split('\n')
    code_lines = [line for line in code_lines if line.strip() != '']
    code = '\n'.join(code_lines)
    return code

def remove_trailing_whitespaces(code):
    code_lines = code.split('\n')
    code_lines = [line.rstrip() for line in code_lines]
    code = '\n'.join(code_lines)
    return code

def generate_prompt(code):
    # Extract code characteristics or relevant information
    code_lines = code.split('\n')
    num_lines = len(code_lines)
    # You can add more code characteristics as per your requirements
    
    # Generate a prompt using the extracted code characteristics
    prompt = f"Please evaluate the technical complexity of the following code:\n\n"
    prompt += f"Code:\n{code}\n\n"
    prompt += f"Code Characteristics:\n"
    prompt += f"- Number of lines: {num_lines}\n"
    # Add more code characteristics if needed
    
    # Add specific questions for code evaluation
    prompt += f"\nQuestions for Evaluation:\n"
    prompt += "- How would you describe the code structure and organization?\n"
    prompt += "- Are there any advanced techniques or algorithms used in the code?\n"
    prompt += "- Can you identify any potential performance bottlenecks or areas for optimization?\n"
    # Add more evaluation questions as per your requirements
    
    return prompt

def assess_code_complexity(code):
    # Preprocess the code as needed before passing it to GPT
    preprocessed_code = preprocess_code(code)

    # Format the GPT prompt by replacing the {code} placeholder with the preprocessed code
    formatted_prompt = generate_prompt(preprocessed_code)

    try:
        # Generate response from GPT
        response = openai.Completion.create(
            engine='text-davinci-003',  # Use the appropriate GPT model
            prompt=formatted_prompt,
            max_tokens=1000,  # Adjust the token limit as needed
            temperature=0.7,  # Adjust the temperature to control response randomness
            n=1,  # Generate a single response
            stop=None,  # Let GPT generate the full response
            timeout=30,  # Set an appropriate timeout value
        )

        # Extract the generated response from GPT
        generated_response = response.choices[0].text.strip()

        # Analyze the generated response to determine the technical complexity of the code
        complexity_score = analyze_generated_response(generated_response)
    except Exception as e:
        print(f"Error during code complexity assessment: {str(e)}")
        complexity_score = ""

    return complexity_score

def fetch_user_repositories(github_url):
    # Extract the username from the GitHub URL
    username = extract_username(github_url)

    if not is_valid_username(username):
        st.error("Invalid GitHub username")
        return []

    try:
        # Get the user object
        user = g.get_user(username)
    except UnknownObjectException:
        st.error("Invalid GitHub username")
        return []

    # Fetch the user's repositories
    repositories = []
    for repo in user.get_repos():
        repositories.append(repo.name)

    return repositories

def extract_username(github_url):
    # Extract the username from the GitHub URL
    username = github_url.split("/")[-1]
    return username

def is_valid_username(username):
    # Check if the username contains only alphanumeric characters and hyphens
    return re.match("^[a-zA-Z0-9-]+$", username) is not None

def evaluate_complexity():
    github_user_url = st.text_input("Enter GitHub Username:")
    if not github_user_url:
        st.warning("Please enter a GitHub Username")
        return

    try:
        user_repositories = fetch_user_repositories(github_user_url)
        complexity_scores = []
        for repository in user_repositories:
            code = fetch_code_from_repository(repository)
            complexity_score = assess_code_complexity(code)
            complexity_scores.append((repository, complexity_score))

        # Sort the repositories based on complexity scores in descending order
        complexity_scores.sort(key=lambda x: x[1], reverse=True)

        if complexity_scores:
            # Get the most technically complex repository
            most_complex_repository, highest_complexity_score = complexity_scores[0]

            # Show the results
            st.success(f"Most complex repository: {most_complex_repository}\nComplexity score: {highest_complexity_score}")
        else:
            # Show a message if no repositories found
            st.warning("No repositories found for the given GitHub user")

    except Exception as e:
        error_message = str(e)
        if "Bad credentials" in error_message:
            st.error("Invalid GitHub credentials. Please check your API token.")
        else:
            st.error(f"Error during code complexity evaluation: {error_message}")

# Run the app
if __name__ == "__main__":
    st.title("Code Complexity Evaluator")
    evaluate_complexity()
