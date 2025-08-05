"""
Defines the MessageHandler class for processing messages in the Streamlit UI.
"""

import streamlit as st
from app.utility.formatting_helpers import format_links
from app.utility.logging import get_logger
from st_config import (CASE_MESSAGES, SPINNER_MESSAGES, OFF_TOPIC_RESPONSE, ERROR_MESSAGES, NO_SPECIALTY_MATCH)
from st_utility import (execute_with_spinner, append_to_conversation, get_conversation_list)
from st_specialty_handler import SpecialtyHandler


# Initialize logger for this module
logger = get_logger(__name__)

class MessageHandler:
    """
    MessageHandler class for processing user messages in the Streamlit application. 
    It handles different cases based on user input and conversation history, including query rewriting and conversational responses.
    It interacts with the LLM handler and specialty handler to generate appropriate responses.
    Attributes:
        llm_handler: Instance of the LLM handler for generating responses.
        specialty_handler: Instance of the SpecialtyHandler for managing specialties.
    Methods:
        handle_case_with_rewrite: Handles cases that require query rewriting.
        handle_conversational_case: Handles conversational cases.
        handle_off_topic_case: Handles off-topic messages.
        handle_new_search_case: Handles new search questions.
        analyze_and_handle_message: Analyzes the message and determines the appropriate case to handle.
    """
    def __init__(self, llm_handler, specialty_handler: 'SpecialtyHandler'):
        logger.info("Initializing MessageHandler")
        self.llm_handler = llm_handler
        self.specialty_handler = specialty_handler
    
    
    def handle_case_with_rewrite(self, case_name: str, user_input: str, conv_history: str, rewrite_method):
        logger.info(f"Handling case with rewrite: {case_name}")
        """
        This method handles cases that require query rewriting. 
        It processes the user input, rewrites the query using the specified method, and generates a response using the pipeline orchestrator.  
        """
        logger.debug(f"Processing {case_name}")
        st.info(f"{case_name} détectée.")
        
        try:
            # Rewrite query using the specified method
            rewritten_query = execute_with_spinner(
                SPINNER_MESSAGES["query_rewrite"], 
                rewrite_method, 
                user_input, 
                conv_history
            )
            logger.debug(f"Rewritten query ({case_name.lower()}): {rewritten_query}")
            current_specialty = self.specialty_handler.get_current_specialty_context()
            
            # Generate response using pipeline with specialty context
            def generate_response():
                from app.services.pipeline_orchestrator_service import PipelineOrchestrator # Import here to avoid circular import
                result, links = PipelineOrchestrator().generate_response(
                    prompt=rewritten_query, 
                    detected_specialty=current_specialty
                )
                return format_links(result, links)
            
            result = execute_with_spinner(SPINNER_MESSAGES["loading"], generate_response)
            append_to_conversation(user_input, result)
            
        except Exception as e:
            logger.error(f"Error in {case_name}: {e}")
            st.error(f"Erreur lors du traitement: {case_name}")
    
    
    def handle_conversational_case(self, case_name: str, user_input: str):
        """
        This method handles conversational cases (case4 and case6).
        It processes the user input, retrieves the current conversation from session state, and generates a response using the LLM handler.
        """
        logger.debug(f"Processing {case_name}")
        st.info(f"{case_name} détectée.")
        
        try:
            # Get current conversation from session state
            current_conversation = get_conversation_list()
            
            # Generate conversational response
            result = execute_with_spinner(
                SPINNER_MESSAGES["loading"], 
                self.llm_handler.continue_conversation, 
                user_input, 
                current_conversation
            )
            append_to_conversation(user_input, result)
            
        except Exception as e:
            logger.error(f"Error in {case_name}: {e}")
            st.error(f"Erreur lors du traitement: {case_name}")
    
    
    def handle_off_topic_case(self, user_input: str):
        """
        Ha
        """
        logger.debug("Processing Case 1: off-topic message")
        st.info(CASE_MESSAGES["case1"])
        append_to_conversation(user_input, OFF_TOPIC_RESPONSE)
    
    
    def handle_new_search_case(self, user_input: str):
        """
        This method handles new search questions (case5). 
        It processes the user input, detects the current specialty context, and generates a response using the pipeline orchestrator.
        If no specialty is detected, it attempts to normalize the specialty format and handle multiple matches.
        If the input is a new question, it generates a response based on the current specialty context.
        If multiple specialties are detected, it prompts the user to select one.
        If no specialty is detected, it defaults to NO_SPECIALTY_MATCH.
        """
        logger.debug("Processing Case 5: new question with search")
        st.info(CASE_MESSAGES["case5"])
        
        try:
            # Get current specialty context
            current_specialty = self.specialty_handler.get_current_specialty_context()
            
            # If no current specialty, try to detect it from the new input
            if not current_specialty or current_specialty == NO_SPECIALTY_MATCH:
                detected_specialty = self.llm_handler.detect_specialty(user_input)
                normalized_specialty = self.specialty_handler.normalize_specialty_format(detected_specialty)
                # Handle multiple matches case
                if normalized_specialty.startswith("multiple matches:"):
                    logger.info("Multiple specialties detected in new search, prompting user for selection")
                    options = self.specialty_handler.extract_specialty_options(normalized_specialty)
                    if options:
                        st.session_state.multiple_specialties = options
                        st.session_state.prompt = user_input  # Store the current prompt
                        st.rerun()
                        return
                    else:
                        # Fallback to no specialty if extraction fails
                        current_specialty = NO_SPECIALTY_MATCH
                else:
                    current_specialty = normalized_specialty if normalized_specialty else NO_SPECIALTY_MATCH
            
            # Generate response using pipeline with specialty context
            def generate_response():
                from app.services.pipeline_orchestrator_service import PipelineOrchestrator # Import here to avoid circular import
                result, links = PipelineOrchestrator().generate_response(
                    prompt=user_input, 
                    detected_specialty=current_specialty
                )
                return format_links(result, links)
            
            result = execute_with_spinner(SPINNER_MESSAGES["loading"], generate_response)
            append_to_conversation(user_input, result)
            
        except Exception as e:
            logger.error(f"Error in new search case: {e}")
            st.error(ERROR_MESSAGES["new_question_processing"])
    
    
    def analyze_and_handle_message(self, user_input: str, conv_history: str):
        """
        Analyze the message and handle it according to the determined case.
        This method uses the LLM handler to analyze the user input and conversation history,
        determines the case, and then calls the appropriate handling method.
        """
        try:
            # Analyze subsequent message using 4-check system
            logger.debug("Analyzing subsequent message using 4-check system")
            analysis = self.llm_handler.analyze_subsequent_message(user_input, conv_history)
            case = self.llm_handler.determine_case(analysis)
            logger.info(f"Determined case: {case}, Analysis: {analysis}")
            
            # Handle different cases
            if case == "case1":
                self.handle_off_topic_case(user_input)
            elif case == "case2":
                self.handle_case_with_rewrite(
                    CASE_MESSAGES["case2"], 
                    user_input, 
                    conv_history, 
                    self.llm_handler.rewrite_query_merge
                )
            elif case == "case3":
                self.handle_case_with_rewrite(
                    CASE_MESSAGES["case3"], 
                    user_input, 
                    conv_history, 
                    self.llm_handler.rewrite_query_add
                )
            elif case == "case4":
                self.handle_conversational_case(CASE_MESSAGES["case4"], user_input)
            elif case == "case5":
                self.handle_new_search_case(user_input)
            else:  # case6
                self.handle_conversational_case(CASE_MESSAGES["case6"], user_input)
                
        except Exception as e:
            logger.error(f"Error during case analysis: {e}")
            st.error(ERROR_MESSAGES["case_analysis"])