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
    sanity_check_message_pertinence_streamlit,
    check_non_french_cities_streamlit,
)
from app.utils.streamlit_helpers import (
    initialize_session_state,
    reset_session_state,
    append_to_conversation,
    create_example_button,
    display_conversation_history,
    format_conversation_history_for_llm,
    execute_with_spinner,
    get_conversation_list,
    get_conversation_length,
    get_session_state_value
)

logger = get_logger(__name__)

class StreamlitChatbot:
    """
    Streamlit-based chatbot UI for hospital ranking queries.
    
    Provides methods to manage session state, handle user input,interact with 
        LLM services, and display conversation history.
        
    Attributes:
        llm_service (LLMService): Service for interacting with the language model.
        MAX_MESSAGES (int): Maximum number of messages in the conversation history. 
    """
    def __init__(self):
        """
        Initialize LLM service and max conversation length.
        """
        
        logger.info("Initializing StreamlitChatbot")
        self.llm_service = LLMService()
        self.MAX_MESSAGES = 5  # Maximum number of messages in the conversation


    def _handle_case_with_rewrite(self, case_name: str, user_input: str, conv_history: str, rewrite_method):
        """
        Helper method to handle cases that require query rewriting.
        
        Args:
            case_name: Name of the case for display
            user_input: User's input message
            conv_history: Conversation history
            rewrite_method: Method to use for query rewriting
        """
        st.info(f"{case_name} détectée.")
        rewritten_query = execute_with_spinner('Réécriture de la requête', rewrite_method, user_input, conv_history)
        logger.debug(f"Rewritten query ({case_name.lower()}): {rewritten_query}")
        self.append_answer(user_input, rewritten_query)

    def _handle_conversational_case(self, case_name: str, user_input: str):
        """
        Helper method to handle conversational cases.
        
        Args:
            case_name: Name of the case for display
            user_input: User's input message
        """
        st.info(f"{case_name} détectée.")
        # Get current conversation from session state using helper
        current_conversation = get_conversation_list()
        result = execute_with_spinner(
            'Chargement', 
            self.llm_service.continue_conversation, 
            user_input, 
            current_conversation
        )
        append_to_conversation(user_input, result)

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
        reset_values = {
            "conversation": [],
            "selected_option": None,
            "prompt": "",
            "specialty": "",
            "city": None,
            "slider_value": None,
        }
        reset_session_state(reset_values)
    
                
    def append_answer(self, prompt, specialty):
        """
        This method interacts with the LLM service to get the final answer based on
            the user's prompt and the selected medical specialty.     
        It formats the response
            and appends it to the conversation history in the session state.
        Args:
            prompt (str): The user's input question or query.
            specialty (str): The medical specialty to filter the response. 
        Returns:
            None: The function updates the session state with the user's prompt and the chatbot's response. 
        """
        def generate_response():
            response = Pipeline().generate_response(prompt=prompt, detected_specialty=specialty)
            if isinstance(response, tuple):
                result, link = response
                if result == 'établissement pas dans ce classement':
                    result = f"Cet hôpital n'est pas présent pour la spécialité {specialty}"
                result = format_links(result, link)
            else:
                result = response
            return result
        
        result = execute_with_spinner('Chargement', generate_response)
        append_to_conversation(prompt, result)
    
    
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
            sanity_check_message_pertinence_streamlit(st.session_state.prompt, self.llm_service, self.reset_session_state, pertinent_chatbot_use_case=False)  
            sanity_check_message_pertinence_streamlit(st.session_state.prompt, self.llm_service, self.reset_session_state, pertinent_chatbot_use_case=True)   
            check_non_french_cities_streamlit(st.session_state.prompt, self.llm_service, self.reset_session_state)
            
        prompt = get_session_state_value("prompt", "")
        if prompt:
            # Detect medical specialty if not already set
            specialty = get_session_state_value("specialty", "")
            if specialty == "":
                st.session_state.specialty = self.llm_service.detect_specialty(prompt)
                specialty = st.session_state.specialty

            if specialty.startswith("multiple matches:"):
                logger.info("Multiple specialties detected, prompting user for selection")
                # Extract options from the string
                options = list(dict.fromkeys(specialty.removeprefix("multiple matches:").strip().split(',')))
                selected_specialty = st.radio("Précisez le domaine médical concerné :", options, index=None)
                
                if selected_specialty:
                    self.append_answer(prompt, selected_specialty)
            else:
                self.append_answer(prompt, specialty)
    
    
    def handle_subsequent_messages(self):
        """
        Handle subsequent messages using 6-case approach.
        This method processes user input using the 4-check system to determine
        how to handle the conversation continuation.
        """    
        user_input = st.chat_input("Votre message")
        if user_input:
            logger.info(f"Processing subsequent message: {user_input[:50]}...")

            # Prepare conversation history for LLM context
            conv_history = format_conversation_history_for_llm()
            logger.debug(f"Conversation history length: {len(conv_history)} characters")

            # Analyze subsequent message using 4-check system
            try:
                logger.debug("Analyzing subsequent message using 4-check system")
                analysis = self.llm_service.analyze_subsequent_message(user_input, conv_history)
                case = self.llm_service.determine_case(analysis)
                logger.info(f"Determined case: {case}, Analysis: {analysis}")
            except Exception as e:
                logger.error(f"Error during case analysis: {e}")
                case = "case6"  # Default to LLM handling
            
            # Handle different cases using helper methods
            case_handlers = {
                "case1": lambda: self._handle_off_topic_case(user_input),
                "case2": lambda: self._handle_case_with_rewrite(
                    "Continuation avec fusion de requête", 
                    user_input, conv_history, 
                    self.llm_service.rewrite_query_merge
                ),
                "case3": lambda: self._handle_case_with_rewrite(
                    "Continuation avec ajout de critères", 
                    user_input, conv_history, 
                    self.llm_service.rewrite_query_add
                ),
                "case4": lambda: self._handle_conversational_case(
                    "Continuation conversationnelle", user_input
                ),
                "case5": lambda: self._handle_new_search_case(user_input),
                "case6": lambda: self._handle_conversational_case(
                    "Nouvelle question conversationnelle", user_input
                )
            }
            
            handler = case_handlers.get(case, case_handlers["case6"])
            handler()

    def _handle_off_topic_case(self, user_input: str):
        """Handle off-topic messages (case1)."""
        st.info("Message hors sujet détecté.")
        result = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler une question relative aux classements des hôpitaux."
        append_to_conversation(user_input, result)

    def _handle_new_search_case(self, user_input: str):
        """Handle new search questions (case5)."""
        st.info("Nouvelle question avec recherche détectée.")
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
        /* Target all buttons in the main content area (not sidebar) */
        .main .stButton > button:first-child {
            background-color: #E3F2FD !important;
            border: 1px solid #BBDEFB !important;
            color: #1976D2 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        .main .stButton > button:first-child:hover {
            background-color: #BBDEFB !important;
            border: 1px solid #90CAF9 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        
        /* Alternative selector targeting by button content */
        button[kind="primary"] {
            background-color: #E3F2FD !important;
            border: 1px solid #BBDEFB !important;
            color: #1976D2 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display example questions as clickable buttons
        st.write("**Exemples de questions :**")
        col1, col2, col3 = st.columns(3)
        
        example_questions = [
            "Quel est le meilleur hôpital de Paris ?",
            "J'ai une gastro-entérite et je suis très inquiet. Où puis-je aller à Lille pour me faire soigner ?",
            "Quels sont les 10 meilleurs hôpitaux publics à Bordeaux pour les maladies cardiaques ?"
        ]
        
        # Create example buttons using helper method
        columns = [col1, col2, col3]
        for i, (col, question) in enumerate(zip(columns, example_questions)):
            with col:
                create_example_button(question, f"example{i+1}")
        
        # Button to start a new conversation
        if st.sidebar.button("🔄 Démarrer une nouvelle conversation"):
            logger.info("User requested new conversation")
            self.reset_session_state()
            st.rerun()
       
        # Initialize session state variables if not already present
        default_values = {
            "conversation": [],
            "selected_option": None,
            "prompt": "",
            "specialty": "",
        }
        initialize_session_state(default_values)
        
        # Check if conversation limit is reached
        check_conversation_limit_streamlit(get_conversation_list(), self.MAX_MESSAGES, self.reset_session_state)
        
        # Handle the first message or subsequent messages
        if get_conversation_length() == 0:
            self.handle_first_message()
        else:
            self.handle_subsequent_messages()
        
        # Display the full conversation history    
        display_conversation_history()      
        
        
            
def main():
    """
    Streamlit entry point.
    """
    chatbot = StreamlitChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
