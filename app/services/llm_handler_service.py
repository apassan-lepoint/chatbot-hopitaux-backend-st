"""
Service for interacting with the language model (LLM).

This file defines the LLMHandler class, which handles all LLM-based extraction of
specialties, cities, institution types, and other information from user queries.
"""

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.config.file_paths_config import PATHS
from app.utility.formatting_helpers import format_mapping_words_csv
from app.utility.logging import get_logger
from app.features.conversation.conversation_manager import ConversationManager


logger = get_logger(__name__)

class LLMHandler:
    """
    Service for interacting with the language model (LLM).  
    
    This service handles all LLM-based extraction of specialties, cities, institution types,
    and other information from user queries, as well as managing conversation history.
    """
    def __init__(self):
        logger.info("LLMHandler __init__ called")
        """
        Initializes the LLMHandler class by loading environment variables, setting up the LLM model with different 
        parameters for the query, and preparing file paths and keyword mappings.
        """
        logger.info("Initializing LLMHandler")
        load_dotenv(override=False) 
        self.model = self.init_model()

        self.paths = PATHS

        # Debug: log the mapping_word_path and list files in the data directory
        logger.info(f"Trying to load mapping_word_path: {self.paths['mapping_word_path']}")
        data_dir = os.path.dirname(self.paths["mapping_word_path"])
        if os.path.exists(data_dir):
            logger.info(f"Files in data directory ({data_dir}): {os.listdir(data_dir)}")
        else:
            logger.warning(f"Data directory does not exist: {data_dir}")

        self.key_words = format_mapping_words_csv(self.paths["mapping_word_path"])

        # Removed PromptDetectionManager usage; now handled in orchestrator
        # Use ConversationManager for all conversation/multi-turn logic
        self.conversation_manager = ConversationManager(self.model)

    
    # Removed extract_prompt_info; prompt detection is now handled in orchestrator
    
    def init_model(self) -> ChatOpenAI:
        """
        Initializes and returns the ChatOpenAI model using the API key from environment variables.
        Returns:
            ChatOpenAI: An instance of the ChatOpenAI model.
        """
        logger.info("init_model called: Initializing ChatOpenAI model")
        api_key = os.getenv("OPENAI_API_KEY")
        logger.debug(f"OPENAI_API_KEY loaded: {'set' if api_key else 'not set'}")
        logger.debug("Creating ChatOpenAI instance")
        self.model = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4o-mini"
        )
        logger.info("ChatOpenAI model initialized")
        return self.model
    

    def run_conversation_checks(self, prompt: str, conv_history: list) -> dict:
        logger.info(f"run_conversation_checks called with prompt: {prompt}, conv_history: {conv_history}")
        """
        Runs all conversation-related checks and consolidates results into a dictionary using ConversationManager.
        """
        logger.debug("Running all conversation checks with ConversationManager")
        return self.conversation_manager.run_all_conversation_checks(prompt, conv_history)

    def rewrite_query_merge(self, prompt: str, conv_history: str) -> str:
        logger.info(f"rewrite_query_merge called with prompt: {prompt}, conv_history: {conv_history}")
        """
        Rewrites the query using the merge approach (Case 2).
        
        Args:
            prompt (str): The user's prompt.
            conv_history (str): The conversation history.
        
        Returns:
            str: The rewritten query using the merge approach.
        """
        logger.debug("Calling rewrite_query_merge on ConversationManager")
        return self.conversation_manager.conversation.rewrite_query_merge(prompt, conv_history)

    def rewrite_query_add(self, prompt: str, conv_history: str) -> str:
        logger.info(f"rewrite_query_add called with prompt: {prompt}, conv_history: {conv_history}")
        """
        Rewrites the query using the add approach (Case 3).
        
        Args:
            prompt (str): The user's prompt.
            conv_history (str): The conversation history.
        
        Returns:
            str: The rewritten query using the add approach.
        """
        logger.debug("Calling rewrite_query_add on ConversationManager")
        return self.conversation_manager.conversation.rewrite_query_add(prompt, conv_history)
