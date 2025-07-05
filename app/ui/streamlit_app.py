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
from datetime import datetime
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


    def _get_current_specialty_context(self):
        """
        Get the current specialty context from session state.
        
        Returns:
            str: The detected specialty or selected specialty from session state
        """
        # Check if user has selected a specialty
        selected_specialty = get_session_state_value("selected_specialty", None)
        if selected_specialty:
            return selected_specialty
        
        # Check specialty context first
        specialty_context = get_session_state_value("specialty_context", None)
        if specialty_context and specialty_context.get("selected_specialty"):
            return specialty_context["selected_specialty"]
        
        # Check if we have a detected specialty (including single specialties from multiple matches)
        detected_specialty = get_session_state_value("specialty", "")
        if detected_specialty and not detected_specialty.startswith(("multiple matches:", "plusieurs correspondances:")):
            return detected_specialty
        
        return ""

    def _normalize_specialty_format(self, specialty: str) -> str:
        """Normalize specialty format to use consistent prefix."""
        if specialty.startswith("plusieurs correspondances:"):
            return specialty.replace("plusieurs correspondances:", "multiple matches:")
        return specialty

    def _extract_specialty_options(self, specialty: str) -> list:
        """Extract specialty options from formatted string."""
        if specialty.startswith("multiple matches:"):
            options_str = specialty.removeprefix("multiple matches:").strip()
        elif specialty.startswith("plusieurs correspondances:"):
            options_str = specialty.removeprefix("plusieurs correspondances:").strip()
        else:
            return []
        
        return list(dict.fromkeys([opt.strip() for opt in options_str.split(',') if opt.strip()]))
    
    
    def _handle_case_with_rewrite(self, case_name: str, user_input: str, conv_history: str, rewrite_method):
        """
        Helper method to handle cases that require query rewriting.
        Matches FastAPI cases 2 and 3.
        
        Args:
            case_name: Name of the case for display
            user_input: User's input message
            conv_history: Conversation history
            rewrite_method: Method to use for query rewriting
        """
        logger.debug(f"Processing {case_name}")
        st.info(f"{case_name} détectée.")
        
        try:
            # Rewrite query using the specified method
            rewritten_query = execute_with_spinner('Réécriture de la requête', rewrite_method, user_input, conv_history)
            logger.debug(f"Rewritten query ({case_name.lower()}): {rewritten_query}")
            
            # Get current specialty context
            current_specialty = self._get_current_specialty_context()
            
            # Generate response using pipeline with specialty context
            def generate_response():
                result, links = Pipeline().generate_response(prompt=rewritten_query, detected_specialty=current_specialty)
                # Format links exactly like FastAPI
                return format_links(result, links)
            
            result = execute_with_spinner('Chargement', generate_response)
            append_to_conversation(user_input, result)
            
        except Exception as e:
            logger.error(f"Error in {case_name}: {e}")
            st.error(f"Erreur lors du traitement: {case_name}")

    def _handle_conversational_case(self, case_name: str, user_input: str):
        """
        Helper method to handle conversational cases.
        Matches FastAPI cases 4 and 6.
        
        Args:
            case_name: Name of the case for display
            user_input: User's input message
        """
        logger.debug(f"Processing {case_name}")
        st.info(f"{case_name} détectée.")
        
        try:
            # Get current conversation from session state
            current_conversation = get_conversation_list()
            
            # Generate conversational response
            result = execute_with_spinner(
                'Chargement', 
                self.llm_service.continue_conversation, 
                user_input, 
                current_conversation
            )
            append_to_conversation(user_input, result)
            
        except Exception as e:
            logger.error(f"Error in {case_name}: {e}")
            st.error(f"Erreur lors du traitement: {case_name}")

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
            "selected_specialty": None,
            "specialty_context": None,
            "multiple_specialties": None,
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
        try:
            def generate_response():
                result, links = Pipeline().generate_response(prompt=prompt, detected_specialty=specialty)
                # Format links exactly like FastAPI
                return format_links(result, links)
            
            result = execute_with_spinner('Chargement', generate_response)
            append_to_conversation(prompt, result)
            
        except Exception as e:
            logger.error(f"Error in append_answer: {e}")
            st.error("Erreur lors de la génération de la réponse.")
    
    
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
            logger.info(f"Received first message - Prompt length: {len(user_input)} chars")
            st.session_state.prompt = user_input
            
            try:
                # Perform sanity checks for first message (no conversation history)
                self._perform_sanity_checks(user_input)
                logger.debug("Sanity checks completed for first message")
                
            except Exception as e:
                logger.error(f"Sanity check failed for first message: {e}")
                return  # Exit early if sanity checks fail
            
        prompt = get_session_state_value("prompt", "")
        if prompt:
            try:
                # Check if user has already selected a specialty from multiple options
                if get_session_state_value("selected_specialty", None) is not None:
                    # User has selected a specialty, use it
                    selected_specialty = st.session_state.selected_specialty
                    logger.info(f"Using previously selected specialty: {selected_specialty}")
                    self.append_answer(prompt, selected_specialty)
                    return
                
                # Check if we're in the middle of specialty selection
                multiple_specialties = get_session_state_value("multiple_specialties", None)
                if multiple_specialties is not None:
                    # Show radio button for specialty selection
                    selected_specialty = st.radio(
                        "Précisez le domaine médical concerné :", 
                        multiple_specialties, 
                        index=None,
                        key="specialty_radio"
                    )
                    
                    if selected_specialty:
                        # Validate that the selected specialty is valid
                        if selected_specialty in multiple_specialties:
                            st.session_state.selected_specialty = selected_specialty
                            st.session_state.specialty_context = {
                                'original_query': prompt,
                                'selected_specialty': selected_specialty,
                                'timestamp': datetime.now().isoformat()
                            }
                            st.session_state.multiple_specialties = None
                            logger.info(f"User selected valid specialty: {selected_specialty}")
                            self.append_answer(prompt, selected_specialty)
                        else:
                            st.error("Sélection invalide. Veuillez choisir une option dans la liste.")
                    return
                
                # Detect medical specialty if not already set
                specialty = get_session_state_value("specialty", "")
                if specialty == "":
                    detected_specialty = self.llm_service.detect_specialty(prompt)
                    # Normalize the format
                    st.session_state.specialty = self._normalize_specialty_format(detected_specialty)
                    specialty = st.session_state.specialty

                if specialty.startswith("multiple matches:"):
                    logger.info("Multiple specialties detected, prompting user for selection")
                    options = self._extract_specialty_options(specialty)
                    if options:
                        st.session_state.multiple_specialties = options
                        st.rerun()
                    else:
                        # Fallback to no specialty if extraction fails
                        self.append_answer(prompt, "aucune correspondance")
                else:
                    # Single specialty detected or no specialty
                    # Handle the case where specialty might be empty or "no specialty match"
                    if not specialty or specialty in ["no specialty match", "aucune correspondance", ""]:
                        specialty = "no specialty match"
                    self.append_answer(prompt, specialty)
                    
            except Exception as e:
                logger.error(f"Error processing first message: {e}")
                st.error("Erreur lors du traitement de votre message.")
    
    
    def handle_subsequent_messages(self):
        """
        Handle subsequent messages using 6-case approach.
        This method processes user input using the 4-check system to determine
        how to handle the conversation continuation.
        """    
        user_input = st.chat_input("Votre message")
        if user_input:
            logger.info(f"Received subsequent message - Prompt length: {len(user_input)} chars, "
                       f"Conversation history: {get_conversation_length()} turns")
            
            try:
                # Perform comprehensive input validation (same as FastAPI)
                current_conversation = get_conversation_list()
                self._perform_sanity_checks(user_input, current_conversation)
                logger.debug("Sanity checks completed for subsequent message")
                
                # Prepare conversation history for LLM analysis (same as FastAPI)
                conv_history = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in current_conversation])
                
                # Analyze and handle message (same as FastAPI)
                self._analyze_and_handle_message(user_input, conv_history)
                
            except Exception as e:
                logger.error(f"Error processing subsequent message: {str(e)}")
                st.error("Une erreur s'est produite lors du traitement de votre message.")

    def _perform_sanity_checks(self, prompt: str, conversation: list = None):
        """
        Perform all sanity checks on user input - matches FastAPI perform_sanity_checks.
        
        Args:
            prompt: The user's input message
            conversation: Optional conversation history for chat endpoints
        Raises:
            Exception: If any sanity check fails, with appropriate error message
        """
        logger.debug("Starting sanity checks for user input")
        
        # Check message length to prevent oversized requests
        check_message_length_streamlit(prompt, self.reset_session_state)
        
        # Prepare conversation history for context-aware checks if available
        conv_history = ""
        if conversation is not None and len(conversation) > 0:
            conv_history = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conversation])
            logger.debug("Checking pertinence with full conversation context")
        else:
            logger.debug("Checking pertinence without conversation context")
        
        # Perform all pertinence checks with conversation context
        sanity_check_message_pertinence_streamlit(prompt, self.llm_service, self.reset_session_state, pertinent_chatbot_use_case=False, conv_history=conv_history)
        sanity_check_message_pertinence_streamlit(prompt, self.llm_service, self.reset_session_state, pertinent_chatbot_use_case=True, conv_history=conv_history)
        
        # Also validate geographical scope using conversation context
        check_non_french_cities_streamlit(prompt, self.llm_service, self.reset_session_state, conv_history=conv_history)
        
        # Check conversation length limits for chat endpoints
        if conversation is not None:
            check_conversation_limit_streamlit(conversation, self.MAX_MESSAGES, self.reset_session_state)
        
        logger.debug("All sanity checks passed successfully")

    def _analyze_and_handle_message(self, user_input: str, conv_history: str):
        """
        Analyze subsequent message and handle based on determined case.
        
        Args:
            user_input: The user's input message
            conv_history: Formatted conversation history for LLM
        """
        try:
            # Analyze subsequent message using 4-check system
            logger.debug("Analyzing subsequent message using 4-check system")
            analysis = self.llm_service.analyze_subsequent_message(user_input, conv_history)
            case = self.llm_service.determine_case(analysis)
            logger.info(f"Determined case: {case}, Analysis: {analysis}")
            
            # Handle different cases (same as FastAPI)
            if case == "case1":
                self._handle_off_topic_case(user_input)
            elif case == "case2":
                self._handle_case_with_rewrite("Continuation avec fusion de requête", user_input, conv_history, self.llm_service.rewrite_query_merge)
            elif case == "case3":
                self._handle_case_with_rewrite("Continuation avec ajout de requête", user_input, conv_history, self.llm_service.rewrite_query_add)
            elif case == "case4":
                self._handle_conversational_case("Continuation LLM", user_input)
            elif case == "case5":
                self._handle_new_search_case(user_input)
            else:  # case6
                self._handle_conversational_case("Nouvelle question LLM", user_input)
                
        except Exception as e:
            logger.error(f"Error during case analysis: {e}")
            st.error("Une erreur s'est produite lors de l'analyse de votre message. Veuillez réessayer.")

    def _handle_off_topic_case(self, user_input: str):
        """
        Handle off-topic messages (case1).
        Matches FastAPI case 1.
        """
        logger.debug("Processing Case 1: off-topic message")
        st.info("Message hors sujet détecté.")
        
        # Use the exact same response as FastAPI
        result = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler une question relative aux classements des hôpitaux."
        append_to_conversation(user_input, result)

    def _handle_new_search_case(self, user_input: str):
        """
        Handle new search questions (case5).
        Matches FastAPI case 5.
        """
        logger.debug("Processing Case 5: new question with search")
        st.info("Nouvelle question avec recherche détectée.")
        
        try:
            # Get current specialty context
            current_specialty = self._get_current_specialty_context()
            
            # Generate response using pipeline with specialty context
            def generate_response():
                result, links = Pipeline().generate_response(prompt=user_input, detected_specialty=current_specialty)
                # Format links exactly like FastAPI
                return format_links(result, links)
            
            result = execute_with_spinner('Chargement', generate_response)
            append_to_conversation(user_input, result)
            
        except Exception as e:
            logger.error(f"Error in new search case: {e}")
            st.error("Erreur lors du traitement de votre nouvelle question.")

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
            "selected_specialty": None,
            "specialty_context": None,
            "multiple_specialties": None,
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
