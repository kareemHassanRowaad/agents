import streamlit as st
from crewai import LLM,Agent, Task, Crew
import os

from langchain_mistralai import ChatMistralAI
import os

# It's best practice to set the API key as an environment variable
os.environ["MISTRAL_API_KEY"] = "aSTlmVLcWwKMH3kCNXGX25U1CKwMNAfo" # Your key



misteral_key = "aSTlmVLcWwKMH3kCNXGX25U1CKwMNAfo"

# --- Page Configuration ---
st.set_page_config(
    page_title="SRS Generator with Human Feedback",
    page_icon="🤖",
    layout="wide"
)

st.title("📄 AI-Powered SRS Generator with Human Feedback")
st.markdown("""
This application uses a team of AI agents to transform your project idea into a detailed Software Requirements Specification (SRS).
You will be asked for feedback to clarify requirements before the final documents are generated.
""")

# Initialize the LLM using the new class
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.5
)

"""
llm = LLM(
    model="mistral/mistral-large-latest",
    temperature=0.5,
    api_key=misteral_key,
)
"""
# --- Session State Initialization ---
if "crew_result" not in st.session_state:
    st.session_state.crew_result = None
if "srs_draft" not in st.session_state:
    st.session_state.srs_draft = None
if "human_answers" not in st.session_state:
    st.session_state.human_answers = None
if "final_use_cases" not in st.session_state:
    st.session_state.final_use_cases = None
if "idea" not in st.session_state:
    st.session_state.idea = ""


# --- Agent Definitions ---
requirements_analyst = Agent(
    role="Requirements Analyst",
    goal="Generate complete Software Requirements Specifications (SRS)",
    backstory="You're a software business analyst with expertise in transforming vague project ideas into full SRS documents.",
    llm=llm,
    verbose=True
)

client_responder = Agent(
    role="Client Interaction Agent",
    goal="Clarify the requirements by asking questions and refining the SRS accordingly",
    backstory="You're responsible for identifying unclear parts of the requirements and interviewing the client to complete the missing details in his project idea.",
    llm=llm,
    verbose=True
)

usecase_engineer = Agent(
    role="Use Case Engineer",
    goal="Convert features in the SRS into technical use case scenarios including actors, flows, and constraints.",
    backstory="You are a seasoned software architect who translates business-level requirements into clear use case definitions.",
    llm=llm,
    verbose=True
)

# --- Streamlit UI and Workflow Logic ---

# Step 1: Get the initial project idea
st.header("Step 1: Describe Your Project Idea")
idea_input = st.text_area("Enter your project idea here (in Arabic or English):", height=150, key="idea_input_area")

if st.button("Generate Initial SRS and Questions", disabled=not idea_input):
    st.session_state.idea = idea_input # Save the idea to session state
    with st.spinner("The Requirements Analyst is drafting the SRS and identifying questions..."):
        task_srs = Task(
            description=(
                f"The client provided the following project idea:\n\n'{st.session_state.idea}'\n\n"
                "Your job is to analyze the idea, extract all the potential software requirements, identify missing or unclear areas, "
                "and then generate a detailed SRS that includes:\n"
                "- Project description\n- Target users\n- Core features\n- Open questions for the client\n- Technical notes or constraints"
            ),
            expected_output="A markdown document for the SRS. It MUST contain a section named 'Open Questions' with questions for the client. (please answer in arabic).",
            agent=requirements_analyst
        )
        temp_crew = Crew(agents=[requirements_analyst], tasks=[task_srs], verbose=True)
        srs_and_questions = temp_crew.kickoff()
        st.session_state.srs_draft = srs_and_questions
        st.session_state.human_answers = None
        st.session_state.final_use_cases = None
        st.rerun() # Rerun to update the UI immediately

# Display the draft SRS and ask for feedback
if st.session_state.srs_draft:
    st.header("Step 2: Provide Your Feedback")
    st.markdown("The AI has generated an initial SRS and has some questions for you. Please review the document and answer the questions below.")
    st.markdown("---")
    st.markdown("### Draft Software Requirements Specification (SRS)")
    st.markdown(st.session_state.srs_draft)
    st.markdown("---")

    st.subheader("Please answer the questions from the document above:")
    answers = st.text_area("Provide your answers here, addressing each question.", height=200, key="human_feedback_area")

    if st.button("Submit Answers and Generate Final Documents", disabled=not answers):
        st.session_state.human_answers = answers
        with st.spinner("The team is updating the SRS and generating the final Use Cases... This may take a moment."):

            # *** FIX IS HERE ***
            # 1. Define a placeholder task_srs object that matches the original.
            #    This ensures the object exists in the current script run.
            task_srs_context = Task(
                description=f"The initial project idea was: {st.session_state.idea}",
                expected_output="Initial SRS with questions.",
                agent=requirements_analyst
            )
            # 2. Manually set its output from our saved state. This is the crucial step
            #    for passing the context to the next task.
            task_srs_context.output = st.session_state.srs_draft

            # Now, define the remaining tasks using the context from our placeholder task
            """task_update = Task(
                description=(
                    "You have an initial SRS and a list of questions that were asked to the client. "
                    f"Here are the client's answers:\n\n'{st.session_state.human_answers}'\n\n"
                    "Your job is to update the initial SRS based on these answers. Refine the requirements, "
                    "fill in the missing details, and remove the 'Open Questions' section."
                ),
                expected_output="The final, updated, and clarified SRS document in markdown format (please answer in arabic).",
                agent=client_responder,
                context=[task_srs_context] # Use the placeholder task for context
            )"""
            # This is the new, correct code
            task_update = Task(
                description=(
                    "You have an initial SRS and a list of questions that were asked to the client. "
                    f"Here are the client's answers:\n\n'{st.session_state.human_answers}'\n\n"
                    "Your job is to update the initial SRS based on these answers. Refine the requirements, "
                    "fill in the missing details, and remove the 'Open Questions' section."
                ),
            expected_output="The final, updated, and clarified SRS document in markdown format (please answer in arabic).",
            agent=client_responder,
            # Directly pass the SRS draft string as context
            context=[st.session_state.srs_draft]
            )


            task_usecases = Task(
                description=(
                    "From the final, updated SRS, extract all the main features and convert each one into a technical Use Case Scenario.\n"
                    "Each scenario must include:\n"
                    "- Title\n- Actors\n- Preconditions\n- Main Flow\n- Alternate Flows (if any)\n- Postconditions\n- Notes"
                ),
                expected_output="A list of technical Use Cases based on the final SRS features (please answer in arabic).",
                agent=usecase_engineer,
                context=[task_update]
            )

            # Create and run the final crew
            final_crew = Crew(
                agents=[client_responder, usecase_engineer],
                tasks=[task_update, task_usecases],
                verbose=True
            )
            final_result = final_crew.kickoff()
            st.session_state.final_use_cases = final_result
            st.rerun() # Rerun to display the final results

# Display the final output
if st.session_state.final_use_cases:
    st.header("Step 3: Final Results")
    st.markdown("The AI team has completed the process based on your feedback.")
    st.markdown("### Final Use Case Scenarios")
    st.markdown(st.session_state.final_use_cases)
    st.success("Process completed successfully!")
