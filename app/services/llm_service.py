"""
Service for interacting with the language model (LLM).

This file defines the LLMService class, which handles all LLM-based extraction of
specialties, cities, institution types, and other information from user queries.
"""

import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.utils.config import PATHS
from app.utils.formatting import format_mapping_words_csv
from app.utils.logging import get_logger

from app.services.query_extraction_service import QueryExtractionService
from app.services.conversation_service import ConversationService
from app.services.multi_turn_service import MultiTurnService

logger = get_logger(__name__)

class LLMService:
    """
    Service for interacting with the language model (LLM).  
    
    This service handles all LLM-based extraction of specialties, cities, institution types,
    and other information from user queries, as well as managing conversation history.
    
    Attributes:
        model (ChatOpenAI): The language model instance used for generating responses.
        paths (dict): Paths to various resources used by the service.
        key_words (dict): Mappings of keywords used for query extraction.
        query_extractor (QueryExtractionService): Service for extracting information from queries.      
        conversation_service (ConversationService): Service for managing conversation history and modifications.
        multi_turn_service (MultiTurnService): Service for handling multi-turn conversations.
    """
    def __init__(self):
        """
        Initializes the LLMService class by loading environment variables, setting up the LLM model with different 
        parameters for the query, and preparing file paths and keyword mappings.
        """
        logger.info("Initializing LLMService")
        load_dotenv(override=False) 
        self.model = self.init_model()
        
        self.paths = PATHS
        self.key_words = format_mapping_words_csv(self.paths["mapping_word_path"])
        
        self.query_extractor = QueryExtractionService(self.model, self.key_words)
        self.conversation_service = ConversationService(self.model)
        self.multi_turn_service = MultiTurnService(self.model)
     
     
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

    def detect_specialty(self, prompt: str) -> str: 
        """
        Determines the medical specialty relevant to the user's question using the LLM.
        
        Args:
            prompt (str): The user's question.
        
        Returns:
            str: The detected specialty or a message indicating no match.
        
        Raises:
            Exception: If the specialty detection fails, an error is logged and raised.
        """
        return self._execute_with_logging(
            "Detecting specialty", 
            prompt, 
            self.query_extractor.detect_specialty_full
        )

    def sanity_check_medical_pertinence(self, prompt: str, conv_history: str = "") -> str:
        """
        Determines if the user's question is off-topic for the assistant.
        
        Args:
            prompt (str): The user's question.
            conv_history (str): Optional conversation history for context.
        
        Returns:
            str: The LLM's off-topic assessment.
        
        Raises:
            Exception: If the medical pertinence check fails, an error is logged and raised.
        """
        return self._execute_with_logging(
            "Checking medical pertinence",
            prompt,
            lambda p: self.query_extractor.sanity_check_medical_pertinence(p, conv_history)
        )

    def sanity_check_chatbot_pertinence(self, prompt: str, conv_history: str = "") -> str: 
        """
        Determines if the user's question is relevant to the hospital ranking assistant.
        
        Args:
            prompt (str): The user's question.
            conv_history (str): Optional conversation history for context.
        
        Returns:
            str: The LLM's assessment of relevance.
        
        Raises:
            Exception: If the chatbot pertinence check fails, an error is logged and raised.
        """
        return self._execute_with_logging(
            "Checking chatbot pertinence",
            prompt,
            lambda p: self.query_extractor.sanity_check_chatbot_pertinence(p, conv_history)
        )

    def detect_city(self, prompt: str, conv_history: str = "") -> str:
        """
        Determines the city mentioned in the user's question.
        
        Args:
            prompt (str): The user's question.
            conv_history (str): Optional conversation history for context.
        
        Returns:
            str: The LLM's city detection result.
        
        Raises:
            Exception: If the city detection fails, an error is logged and raised.
        """
        return self._execute_with_logging(
            "Detecting city",
            prompt,
            lambda p: self.query_extractor.detect_city(p, conv_history)
        )

    def detect_topk(self, prompt: str):
        """
        Identifies if the number of institutions to display is mentioned in the user's question.
        Returns integer for top-k or 'non mentionné' if not mentioned.
        """
        def _detect_topk_with_fallback(prompt: str):
            topk = self.query_extractor.detect_topk(prompt)
            return topk if topk > 0 else 'non mentionné'
        
        return self._execute_with_logging(
            "Detecting top_k",
            prompt,
            _detect_topk_with_fallback
        )

    def detect_institution_type(self, prompt: str) -> str:
        """
        Determines if the user's question mentions a public or private institution, or a specific institution.
        
        Args:
            prompt (str): The user's question.
        
        Returns:
            str: The detected institution type or name.
            
        Raises:
            Exception: If the institution type detection fails, an error is logged and raised.
        """
        return self._execute_with_logging(
            "Detecting institution type",
            prompt,
            self.query_extractor.detect_institution_type
        )  

    
    @property
    def institution_name(self):
        return self.query_extractor.institution_name

    
    @property
    def institution_mentioned(self):
        return self.query_extractor.institution_mentioned
    
    
    def continue_conversation(self, prompt: str, conv_history: list) -> str:
        """
        Generates a response to the user's new question, taking into account the conversation history.
        
        Args:
            prompt (str): The user's new question.
            conv_history (list): The conversation history.
        
        Returns:
            str: The LLM's generated response.
        """
        logger.info(f"Continuing conversation with prompt: {prompt}")
        logger.debug(f"Conversation history: {conv_history}")
        return self.conversation_service.continue_conversation(prompt, conv_history)

    def detect_modification(self, prompt: str, conv_history: list) -> str:
        """
        Detects if the user's new question is a modification of the last question or a new question.
        
        Args:
            prompt (str): The user's new question.
            conv_history (list): The conversation history.
        
        Returns:
            str: The LLM's response indicating whether it's a modification or a new question.
        """
        return self.conversation_service.detect_query_modification(prompt, conv_history)

    def rewrite_query(self, last_query: str, modification: str) -> str:
        """
        Rewrites the last query based on the detected modification.
        
        Args:
            last_query (str): The last query made by the user.
            modification (str): The detected modification to the last query.
        
        Returns:
            str: The rewritten query based on the modification.
        """
        return self.conversation_service.rewrite_modified_query(last_query, modification)

    # Multi-turn conversation methods
    def analyze_subsequent_message(self, prompt: str, conv_history: str) -> Dict[str, Any]:
        """
        Analyzes subsequent message using 4-check system.
        
        Args:
            prompt: User's subsequent message
            conv_history: Formatted conversation history
            
        Returns:
            Dict containing case analysis results
        """
        return self.multi_turn_service.analyze_subsequent_message(prompt, conv_history)

    def determine_case(self, analysis: Dict[str, Any]) -> str:
        """Determine which case applies based on analysis."""
        return self.multi_turn_service.determine_case(analysis)

    def rewrite_query_merge(self, prompt: str, conv_history: str) -> str:
        """Rewrite query using merge approach (Case 2)."""
        return self.conversation_service.rewrite_query_merge(prompt, conv_history)

    def rewrite_query_add(self, prompt: str, conv_history: str) -> str:
        """Rewrite query using add approach (Case 3)."""
        return self.conversation_service.rewrite_query_add(prompt, conv_history)
