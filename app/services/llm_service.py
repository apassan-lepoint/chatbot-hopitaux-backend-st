"""
Service for interacting with the language model (LLM).

This file defines the LLMService class, which handles all LLM-based extraction of
specialties, cities, institution types, and other information from user queries.
"""

import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.utils.config import PATHS
from app.utils.formatting import format_mapping_words_csv
from app.utils.logging import get_logger

from app.services.query_extraction_service import QueryExtractionService
from app.services.conversation_service import ConversationService

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
    Methods:
        init_model() -> ChatOpenAI:
            Initializes and returns the ChatOpenAI model using the API key from environment variables.
        detect_specialty(prompt: str) -> str:
            Determines the medical specialty relevant to the user's question using the LLM.
        sanity_check_medical_pertinence(prompt: str) -> str:
            Determines if the user's question is off-topic for the assistant.
        sanity_check_chatbot_pertinence(prompt: str) -> str:
            Determines if the user's question is relevant to the hospital ranking assistant.    
        detect_city(prompt: str) -> str:
            Identifies the city or department mentioned in the user's question.
        detect_topk(prompt: str):
            Identifies if the number of institutions to display is mentioned in the user's question.
        detect_institution_type(prompt: str) -> str:
            Determines if the user's question mentions a public or private institution, or a specific institution.
        continue_conversation(prompt: str, conv_history: list) -> str:          
            Generates a response to the user's new question, taking into account the conversation history.
        detect_modification(prompt: str, conv_history: list) -> str:
            Detects if the user's new question is a modification of the last question or a new question.
        rewrite_query(last_query: str, modification: str) -> str:
            Rewrites the last query based on the detected modification. 
    """
    def __init__(self):
        """
        Initializes the LLMService class by loading environment variables, setting up the LLM model with different 
            parameters for the query, and preparing file paths and keyword mappings.
        """
        logger.info("Initializing LLMService")
        load_dotenv(override = False) 
        self.model = self.init_model()
        
        self.paths = PATHS
        self.key_words = format_mapping_words_csv(self.paths["mapping_word_path"])
        
        self.query_extractor = QueryExtractionService(self.model, self.key_words)
        self.conversation_service = ConversationService(self.model)
     
     
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
        
    
    def detect_specialty(self, prompt: str) -> str: #work to simplify this function; did it give a specialty; and if so give a list ==> fully as JSON
        """
        Determines the medical specialty relevant to the user's question using the LLM.
        
        Args:
            prompt (str): The user's question.
        
        Returns:
            str: The detected specialty or a message indicating no match.
        
        Raises:
            Exception: If the specialty detection fails, an error is logged and raised.
        """
        logger.info(f"Detecting specialty for prompt: {prompt[:50]}...")
        try:
            specialty = self.query_extractor.detect_specialty_full(prompt)
            logger.debug(f"Specialty detection result: {specialty}")
            return specialty
        except Exception as e:
            logger.error(f"Specialty detection failed: {e}")
            raise

    
    def sanity_check_medical_pertinence(self, prompt: str) -> str:
        """
        Determines if the user's question is off-topic for the assistant.
        
        Args:
            prompt (str): The user's question.
        
        Returns:
            str: The LLM's off-topic assessment.
        Raises:
            Exception: If the medical pertinence check fails, an error is logged and raised.
        """
        logger.info(f"Checking medical pertinence for prompt: {prompt[:50]}...")
        try:
            result = self.query_extractor.sanity_check_medical_pertinence(prompt)
            logger.debug(f"Medical pertinence check result: {result}")
            return result
        except Exception as e:
            logger.error(f"Medical pertinence check failed: {e}")
            raise
        
    
    
    def sanity_check_chatbot_pertinence(self, prompt: str) -> str: 
        """
        Determines if the user's question is relevant to the hospital ranking assistant.
        
        Args:
            prompt (str): The user's question.
        
        Returns:
            str: The LLM's assessment of relevance.
        
        Rqises:
            Exception: If the chatbot pertinence check fails, an error is logged and raised.
        """
        logger.info(f"Checking chatbot pertinence for prompt: {prompt[:50]}...")
        try:
            result = self.query_extractor.sanity_check_chatbot_pertinence(prompt)
            logger.debug(f"Chatbot pertinence check result: {result}")
            return result
        except Exception as e:
            logger.error(f"Chatbot pertinence check failed: {e}")
            raise

    
    def detect_city(self, prompt: str) -> str:
        """
        Identifies the city or department mentioned in the user's question.
        Handles ambiguous cases with a two-step LLM process.
        Args:
            prompt (str): The user's question.
        Returns:
            str: The detected city or department.
            
        Raises:
            Exception: If the city detection fails, an error is logged and raised.
        """
        logger.info(f"Detecting city for prompt: {prompt[:50]}...")
        try:
            city = self.query_extractor.detect_city(prompt)
            logger.debug(f"City detection result: {city}")
            return city
        except Exception as e:
            logger.error(f"City detection failed: {e}")
            raise

    
    def detect_topk(self, prompt: str):
        """
        Identifies if the number of institutions to display is mentioned in the user's question.
        Returns integer for top-k or 'non mentionné' if not mentioned.
        """
        logger.info(f"Detecting top_k for prompt: {prompt[:50]}...")
        try:
            topk = self.query_extractor.detect_topk(prompt)
            logger.debug(f"Top_k detection result: {topk}")
            return topk if topk > 0 else 'non mentionné'
        except Exception as e:
            logger.error(f"Top_k detection failed: {e}")
            raise
        
    
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
        logger.info(f"Detecting institution type for prompt: {prompt[:50]}...")
        try:
            institution_type = self.query_extractor.detect_institution_type(prompt)
            logger.debug(f"Institution type detection result: {institution_type}")
            return institution_type
        except Exception as e:
            logger.error(f"Institution type detection failed: {e}")
            raise  

    
    @property
    def institution_name(self):
        return self.query_extractor.institution_name

    
    @property
    def institution_mentioned(self):
        return self.query_extractor.institution_mentioned
    
    
    def continue_conversation(self, prompt: str , conv_history: list) -> str:
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
