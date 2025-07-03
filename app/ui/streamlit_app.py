"""
Streamlit-based user interface for the hospital ranking chatbot.

This file defines the StreamlitChatbot class and main UI logic, enabling interactive
    conversations with the chatbot and displaying results in a web app.
"""

import sys
import os

# Go 2 levels up to add the repo root to sys.path
# This needs to happen before importing any modules from the repo
current_dir = os.path.dirname(__file__)
repo_root = os.path.abspath(os.path.join(current_dir, "../../"))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import streamlit as st
from app.services.pipeline_service import Pipeline
from app.services.llm_service import LLMService
from app.utils.formatting import format_links
from app.utils.logging import get_logger
from app.utils.sanity_checks.streamlit_sanity_checks import (
    check_message_length_streamlit,
    check_conversation_limit_streamlit,
    check_message_pertinence_streamlit,
    check_non_french_cities_streamlit,
)

logger = get_logger(__name__)

class StreamlitChatbot:
    """
    Streamlit-based chatbot UI for hospital ranking queries.
    
    Provides methods to manage session state, handle user input,interact with 
        LLM services, and display conversation history.
    """
    def __init__(self):
        """
        Initialize LLM service and max conversation length.
        """
        
        logger.info("Initializing StreamlitChatbot")
        self.llm_service = LLMService()
        self.MAX_MESSAGES = 10  # Maximum number of messages in the conversation


    def reset_session_state(self):
        """
        Reset all session state variables.
        This method clears the conversation history, selected options, user prompt,
            and other related variables in the Streamlit session state.
        Args:
            self: The instance of the StreamlitChatbot class.   
        Returns:
            None: The function updates the session state to clear the conversation history
                and other related variables.
        """
        logger.info("Resetting session state")
        for key, value in {
            "conversation": [],
            "selected_option": None,
            "prompt": "",
            "speciality": "",
            "city": None,
            "slider_value": None,
        }.items():
            st.session_state[key] = value
    
        
    def display_conversation(self):
        """
        Display the conversation history with chat-like styling.
        """
        for user, bot in st.session_state.conversation:
            st.chat_message("user").write(user)
            st.chat_message("assistant").write(bot, unsafe_allow_html=True)
    
                
    def append_answer(self, prompt, speciality):
        """
        This method interacts with the LLM service to get the final answer based on
            the user's prompt and the selected medical specialty.     
        It formats the response
            and appends it to the conversation history in the session state.
        Args:
            prompt (str): The user's input question or query.
            speciality (str): The medical specialty to filter the response. 
        Returns:
            None: The function updates the session state with the user's prompt and the chatbot's response. 
        """
        with st.spinner('Chargement'):
            response = Pipeline().final_answer(prompt=prompt, specialty_st=speciality)
            if isinstance(response, tuple):
                result, link = response
                if result == 'établissement pas dans ce classement':
                    result = f"Cet hôpital n'est pas présent pour la spécialité {speciality}"
                result = format_links(result, link)
            else:
                result = response
        st.session_state.conversation.append((prompt, result))
    
    
    def handle_first_message(self):
        """
        This function handles the first message in the conversation.        
        It initializes the conversation, checks message length, and processes
            the user input to determine the medical specialty and provide an answer.
        Args:
            self: The instance of the StreamlitChatbot class.      
        Returns:
            None: The function updates the session state with the user's prompt and the chatbot's response.
        """
        user_input = st.chat_input("Votre message")
        if user_input:
            logger.info(f"User input: {user_input}")
            st.session_state.prompt = user_input
            check_message_length_streamlit(st.session_state.prompt, self.reset_session_state)
            check_message_pertinence_streamlit(st.session_state.prompt, self.llm_service, self.reset_session_state, pertinence_check2=False)  
            check_message_pertinence_streamlit(st.session_state.prompt, self.llm_service, self.reset_session_state, pertinence_check2=True)   
            check_non_french_cities_streamlit(st.session_state.prompt, self.llm_service, self.reset_session_state)
            
        if st.session_state.prompt:
            # Detect medical specialty if not already set
            if st.session_state.speciality == "":
                st.session_state.speciality = self.llm_service.detect_specialty(st.session_state.prompt)

            speciality = st.session_state.speciality
            if speciality.startswith("plusieurs correspondances:"):
                logger.info("Multiple specialties detected, prompting user for selection")
                # Extract options from the string
                options = list(dict.fromkeys(speciality.removeprefix("plusieurs correspondances:").strip().split(',')))
                selected_specialty = st.radio("Précisez le domaine médical concerné :", options, index=None)
                if selected_specialty:
                    self.append_answer(st.session_state.prompt, selected_specialty)
            else:
                self.append_answer(st.session_state.prompt, speciality)
    
    
    def handle_subsequent_messages(self):
        """
        Handle subsequent messages in the conversation.
        This method processes user input, checks for medical specialties, and
        generates responses based on the conversation history.
        Args:
            self: The instance of the StreamlitChatbot class.
        Returns:
            None: The function updates the session state with the user's prompt and the chatbot's response.
        """    
        user_input = st.chat_input("Votre message")
        if user_input:
            logger.info(f"User input received: {user_input}")

            # Prepare conversation history for LLM context
            conv_history = "\n".join(
                [f"Utilisateur: {q}\nAssistant: {r}" for q, r in st.session_state.conversation]
            ) if hasattr(st.session_state, "conversation") else ""

            # Use LLM to detect if this is a modification or a new query
            try:
                mod_type = self.llm_service.detect_modification(user_input, conv_history)
                logger.info(f"Detected query type: {mod_type}")
            except Exception as e:
                logger.error(f"Error during modification detection: {e}")
                mod_type = "nouvelle question"
            
            if mod_type == "ambiguous":
                user_choice = st.radio(
                    "Je ne suis pas sûr si votre message est une nouvelle question ou une modification de la précédente. Veuillez préciser :",
                    ("Continuer la conversation précédente", "Poser une nouvelle question")
                )
                mod_type = "modification" if user_choice == "Continuer la conversation précédente" else "nouvelle question"
            
            if mod_type == "modification":
                st.info("Modification détectée de la question précédente.")
                last_user_query = next((msg for msg, _ in reversed(st.session_state.conversation) if msg), None)
                full_query = self.llm_service.rewrite_query(last_user_query, user_input)
                self.append_answer(user_input, full_query)
                
            # Handle new query
            else:
                st.info("Nouvelle question détectée.")
                self.append_answer(user_input, user_input)
    
    
    def run(self):
        """
        Run the Streamlit application.    
        This method initializes the UI, handles user input, and manages the conversation
        history.
        """
        logger.info("Running StreamlitChatbot application")
        st.title("Assistant Hôpitaux")
        st.write("Posez votre question ci-dessous.")
        
        # Add custom CSS for light blue button background
        st.markdown("""
        <style>
        .stButton > button[key^="example"] {
            background-color: #E3F2FD !important;
            border: 1px solid #BBDEFB !important;
            color: #1976D2 !important;
        }
        .stButton > button[key^="example"]:hover {
            background-color: #BBDEFB !important;
            border: 1px solid #90CAF9 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display example questions as clickable buttons
        st.write("**Exemples de questions :**")
        col1, col2, col3 = st.columns(3)
        
        example_questions = [
            "Quel est le meilleur hôpital de Paris ?",
            "J'ai une gastro-entérite et je suis très inquiet. Où puis-je aller à Lille pour me faire soigner ?",
            "Quels sont les 10 meilleurs hôpitaux privés à Bordeaux pour les maladies cardiaques ?"
        ]
        
        with col1:
            if st.button(example_questions[0], key="example1", help="Cliquez pour poser cette question"):
                # Set prompt and trigger processing
                st.session_state.prompt = example_questions[0]
                # Display the question in chat immediately
                st.chat_message("user").write(example_questions[0])
                st.rerun()
        with col2:
            if st.button(example_questions[1], key="example2", help="Cliquez pour poser cette question"):
                # Set prompt and trigger processing
                st.session_state.prompt = example_questions[1]
                # Display the question in chat immediately
                st.chat_message("user").write(example_questions[1])
                st.rerun()
        with col3:
            if st.button(example_questions[2], key="example3", help="Cliquez pour poser cette question"):
                # Set prompt and trigger processing
                st.session_state.prompt = example_questions[2]
                # Display the question in chat immediately
                st.chat_message("user").write(example_questions[2])
                st.rerun()
        
        # Button to start a new conversation
        if st.sidebar.button("🔄 Démarrer une nouvelle conversation"):
            logger.info("User requested new conversation")
            self.reset_session_state()
            st.rerun()
       
        # Initialize session state variables if not already present
        for key, value in {
            "conversation": [],
            "selected_option": None,
            "prompt": "",
            "speciality": "",
        }.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        # Check if conversation limit is reached
        check_conversation_limit_streamlit(st.session_state.conversation, self.MAX_MESSAGES, self.reset_session_state)
        
        # Handle the first message or subsequent messages
        if len(st.session_state.conversation) == 0:
            self.handle_first_message()
        else:
            self.handle_subsequent_messages()
        
        # Display the full conversation history    
        self.display_conversation()      
        
        
            
def main():
    """
    Streamlit entry point.
    """
    chatbot = StreamlitChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
