import streamlit as st
from crewai import LLM,Agent, Task, Crew
import os
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource



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




llm = LLM(
    model="mistral/mistral-large-latest",
    temperature=0.5,
    api_key=misteral_key,
)

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

# Create a knowledge source
content = """
            You are software business analyst expert +10 years experience.
            you are working in Rowaad company which is from biggest software companies for technology in Saudia arabia and Egypt.
            Rowaad Establishment, a formal Saudi institution specializing in providing comprehensive web services and hosting solutions.
            our services include website, application, and e-commerce store design and programming, as well as digital marketing and design services.
"""

string_source = StringKnowledgeSource(content = content)
embedder={
        "provider": "google",
        "config": {
            "model": "models/text-embedding-004",
            "api_key": "AIzaSyBT0UYBqJN-ycgguvS5eaAqNS1nUvgoPLA"
        }
    }

specialist_source = StringKnowledgeSource(content="You are working on usecase according to the knowledge source as an outline for your generated usecases")

specialist_knowledge = TextFileKnowledgeSource(
    file_paths=["env_example.txt"]
)

# --- Agent Definitions ---
requirements_analyst = Agent(
    role="Requirements Analyst",
    goal="Generate complete Software Requirements Specifications (SRS)",
    backstory="You're a software business analyst with expertise in transforming vague project ideas into full SRS documents" + \
              "Normally you are on software solutions depends on mobile native (Android and IOS) using kotlin and swift sometimes may we need website and finally dashboard for management and to control data dynamically inside apps"+ \
              "You are professinal your role to discover the missing parts and inspire the client to to get him on the track."
              ,
    llm=llm,
    verbose=True
)

client_responder = Agent(
    role="Client Interaction Agent",
    goal="Clarify the requirements by asking questions and refining the SRS accordingly",
    backstory="You're responsible for identifying unclear parts of the requirements and interviewing the client to complete the missing details in his major thrusts." ,
    llm=llm,
    verbose=True
)

usecase_engineer = Agent(
    role="Use Case Engineer",
    goal="Convert features in the SRS into technical use case scenarios including actors, flows, and constraints for each platform depends on user demands."+ \
         "Your mission to create all usecases from a to z on each part(platform) of the system mobile,dashboard and web if it exist depends on needs.",
    backstory="You are senior software architect who translates business-level requirements into clear use case definitions.",
    llm=llm,
    verbose=True
)

# --- Streamlit UI and Workflow Logic ---

# Step 1: Get the initial project idea
st.header("Step 1: Describe Your Project Idea")
idea_input = st.text_area("Enter your project idea here (in Arabic or English):", height=150, key="idea_input_area")

if st.button("Generate Initial SRS and Questions 🚀", disabled=not idea_input):
    st.session_state.idea = idea_input # Save the idea to session state
    with st.spinner("The Requirements Analyst is drafting the SRS and identifying questions..."):
        task_srs = Task(
            description=(
                f"The client provided the following project idea:\n\n'{st.session_state.idea}'\n\n"
                "Your job is to analyze the idea,infere and suggest the systems requirements of technology and platforms to build the system then extract all the potential software requirements, identify missing or unclear areas, from your experience suggest the system requirements and show them to user in Open questions section with suggestions"
                "and then generate a detailed SRS that includes:\n"
                "- Project description\n- Target users\n- Core features\n- Open questions for the client\n- System architecture (platforms and technologies)"
            ),
            expected_output="A markdown document for the SRS. It MUST contain a section named 'Open Questions' with questions for the client. (please answer in arabic).",
            agent=requirements_analyst
        )

        temp_crew = Crew(agents=[requirements_analyst],knowledge_sources=[string_source],embedder=embedder, tasks=[task_srs], verbose=True)
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
            task_update = Task(
                description=(
                    "You have an initial SRS and a list of questions that were asked to the client. "
                    f"Here are the client's answers:\n\n'{st.session_state.human_answers}'\n\n"
                    "Your job is to update the initial SRS based on these answers. Refine the requirements, "
                    "fill in the missing details, update the features according to his answers and remove the 'Open Questions' section."
                ),
                expected_output="The final, updated, and clarified SRS document in markdown format (please answer in arabic).",
                agent=client_responder,
                context=[task_srs_context] # Use the placeholder task for context
            )

            task_usecases = Task(
                description=(
                    """
                    When generating the Software Requirements Specification (SRS) and related Use Case Scenarios, you must differentiate between two categories of features:
                    Core Features:
                        These are the functional capabilities explicitly extracted from the client’s project idea.
                    Your task is to analyze the client’s description and identify all features that are unique or specific to their intended solution.
                    Map each identified feature to the appropriate category in the Core Functions.
                    Preserve the client’s own terminology where relevant, but ensure each function is clearly described in technical terms.
                    Static (Common) Features:
                        These are general-purpose capabilities that exist in most mobile applications regardless of the client’s specific domain.
                    Examples include, but are not limited to:
                    Authentication (Login, Registration, OTP verification, Forgot Password)
                    Main Menu / Navigation Drawer
                    User Profile Management
                    Application Settings
                    Notifications (Push and in-app)
                    Digital Wallet or Balance Management (if applicable you detect that)
                    Favorites / Bookmarks / Wishlists (if applicable you detect that)
                    Contact & Support modules
                    Consequently there are some features must be exist in any dashboard and must fulfill in the app:
                     - data mangement
                     - users mangement
                     - viewing statics & analytics
                     - review the complains & suggestions
                     - provide essentials info for the policy/about app/terms and contact info dynamically.
                    These must be automatically included in the SRS and Use Cases for every relevant platform, even if the client did not explicitly mention them, unless explicitly excluded by the client.
                    Requirements for Integration:
                        Clearly separate core functions from static features in your internal processing, but present them in a unified, coherent structure in the final SRS.
                        Consider each screen as a feature so you should mention each screen inside the system.
                        In Use Case generation, ensure both core and static features are fully represented with complete actors, preconditions, flows, and postconditions.
                        For each platform (e.g., Android, iOS, Web, Dashboard), append all relevant static features to the platform-specific SRS section and generate matching Use Cases.
                        When merging, avoid duplication by consolidating overlapping functionality from the client’s core features and the static feature set.
                        Document in the SRS which features are derived from the client’s requirements and which are added as standard static features.
                    So,i expected to merge the results of previous tasks with current to generate for (mobile and admin panel):
                        - Project description\n- Target users\n- (Core + Static) features for (moile) \n- (Core + Static) features for (admin panel)\n- Journey of each expected user type in the app.
"""
                ),
                expected_output="Write all details of technical UseCases for each screen regarding the required (platforms) based on the final SRS features (please answer in arabic).",
                agent=usecase_engineer,
                Markdown=True,
                context=[task_update]
            )

            # Create and run the final crew
            final_crew = Crew(
                agents=[client_responder, usecase_engineer],
                tasks=[task_update, task_usecases],
                knowledge_sources=[string_source,specialist_knowledge],
                embedder=embedder,
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
