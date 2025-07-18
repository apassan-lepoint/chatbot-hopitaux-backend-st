"""
Service for interacting with the language model (LLM).

This file defines the LLMHandler class, which handles all LLM-based extraction of
specialties, cities, institution types, and other information from user queries.
"""

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from config.file_paths_config import PATHS
from app.utility.formatting_helpers import format_mapping_words_csv
from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_and_parse_boolean
from app.utility.wrappers import prompt_formatting


from app.features.prompt_detection.prompt_detection_manager import PromptDetectionManager
from app.features.conversation.conversation_manager import ConversationManager

from app.features.prompt_detection.topk_detection import TopKDetector


logger = get_logger(__name__)

class LLMHandler:
    """
    Service for interacting with the language model (LLM).  
    
    This service handles all LLM-based extraction of specialties, cities, institution types,
    and other information from user queries, as well as managing conversation history.
    """
    def __init__(self):
        """
        Initializes the LLMHandler class by loading environment variables, setting up the LLM model with different 
        parameters for the query, and preparing file paths and keyword mappings.
        """
        logger.info("Initializing LLMHandler")
        load_dotenv(override=False) 
        self.model = self.init_model()
        
        self.paths = PATHS
        self.key_words = format_mapping_words_csv(self.paths["mapping_word_path"])
        
        self.prompt_manager = PromptDetectionManager(self.model)
        self.topk_detector = TopKDetector(self.model)
        # Use ConversationManager for all conversation/multi-turn logic
        self.conversation_manager = ConversationManager(self.model)
     
    
    def extract_prompt_info(self, prompt: str, conv_history: str = "", institution_list=None, k=3) -> Dict[str, Any]:
        """
        Extracts all relevant information from a prompt using PromptDetectionManager.
        Returns a consolidated dictionary with city, specialty, top_k, institution name, and institution type.
        """
        results = self.prompt_manager.run_all_detections(prompt, conv_history, institution_list)
        specialty_top_k = None
        if hasattr(self.prompt_manager.specialty_detector, 'detect_specialty'):
            specialty_result = self.prompt_manager.specialty_detector.detect_specialty(prompt, conv_history)
            if hasattr(specialty_result, 'specialty_list'):
                specialty_top_k = specialty_result.specialty_list[:k]
            else:
                specialty_top_k = [specialty_result]
        results['specialty_top_k'] = specialty_top_k
        return results
    
    def init_model(self) -> ChatOpenAI:
        """
        Initializes and returns the ChatOpenAI model using the API key from environment variables.
        Returns:
            ChatOpenAI: An instance of the ChatOpenAI model.
        """
        logger.info("Initializing ChatOpenAI model")
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4o-mini"
        )
        logger.info("ChatOpenAI model initialized")
        return self.model
        
    
    def _execute_with_logging(self, operation_name: str, prompt: str, operation_func, *args, **kwargs):
        """
        Generic method to execute operations with consistent logging and error handling.
        
        Args:
            operation_name (str): Name of the operation for logging
            prompt (str): The user's prompt
            operation_func: The function to execute
            *args: Additional arguments for the operation function
            **kwargs: Additional keyword arguments for the operation function
        
        Returns:
            The result of the operation function
        
        Raises:
            Exception: If the operation fails, an error is logged and raised.
        """
        logger.info(f"{operation_name} for prompt: {prompt[:50]}...")
        try:
            result = operation_func(prompt, *args, **kwargs)
            logger.debug(f"{operation_name} result: {result}")
            return result
        except Exception as e:
            logger.error(f"{operation_name} failed: {e}")
            raise

    def sanity_check_medical_pertinence(self, prompt: str, conv_history: str = "") -> str:
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Returns True if medically pertinent, False otherwise.
        Args:
            prompt: The message to check
            conv_history: Optional conversation history for context
        """
        formatted_prompt = prompt_formatting(
            "sanity_check_medical_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "sanity_check_medical_pertinence")

    def sanity_check_chatbot_pertinence(self, prompt: str, conv_history: str = "") -> str:
        """
        Checks the pertinence of the given prompt for the chatbot using the LLM.
        Returns True if relevant to chatbot, False otherwise.
        Args:
            prompt: The message to check
            conv_history: Optional conversation history for context
        """
        from app.utility.wrappers import prompt_formatting
        formatted_prompt = prompt_formatting(
            "sanity_check_chatbot_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "sanity_check_chatbot_pertinence")


    def rewrite_query(self, last_query: str, modification: str) -> str:
        """
        Rewrites the last query based on the detected modification.
        
        Args:
            last_query (str): The last query made by the user.
            modification (str): The detected modification to the last query.
        
        Returns:
            str: The rewritten query based on the modification.
        """
        return self.conversation_manager.conversation.rewrite_modified_query(last_query, modification)

    def run_conversation_checks(self, prompt: str, conv_history: list) -> dict:
        """
        Runs all conversation-related checks and consolidates results into a dictionary using ConversationManager.
        """
        return self.conversation_manager.run_all_conversation_checks(prompt, conv_history)

    def rewrite_query_merge(self, prompt: str, conv_history: str) -> str:
        """
        Rewrites the query using the merge approach (Case 2).
        
        Args:
            prompt (str): The user's prompt.
            conv_history (str): The conversation history.
        
        Returns:
            str: The rewritten query using the merge approach.
        """
        return self.conversation_manager.conversation.rewrite_query_merge(prompt, conv_history)

    def rewrite_query_add(self, prompt: str, conv_history: str) -> str:
        """
        Rewrites the query using the add approach (Case 3).
        
        Args:
            prompt (str): The user's prompt.
            conv_history (str): The conversation history.
        
        Returns:
            str: The rewritten query using the add approach.
        """
        return self.conversation_manager.conversation.rewrite_query_add(prompt, conv_history)
