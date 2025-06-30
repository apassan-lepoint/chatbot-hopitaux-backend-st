"""
Service for interacting with the language model (LLM).

This file defines the LLMService class, which handles all LLM-based extraction of
specialties, cities, institution types, and other information from user queries.
"""

import os
from langchain_openai import ChatOpenAI
import pandas as pd
from dotenv import load_dotenv

from app.utils.config import PATHS
from app.utils.query_detection.specialties import (
    specialty_list,
    specialty_categories_dict,
    extract_specialty_keywords,
)
from app.utils.formatting import format_mapping_words_csv, format_correspondance_list
from app.utils.logging import get_logger

from app.services.query_extraction_service import QueryExtractionService
from app.services.conversation_service import ConversationService

logger = get_logger(__name__)

class LLMService:
    """
    Handles all interactions with the language model (LLM) for extracting relevant information
        from user queries/prompts. 
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
        """
        logger.info(f"Detecting specialty for prompt: {prompt}")
        specialty = self.query_extractor.detect_speciality_full_query_ext_service(prompt)
        logger.debug(f"Detected specialty: {specialty}")
        return specialty

    def check_medical_pertinence(self, prompt: str) -> str:
        """
        Determines if the user's question is off-topic for the assistant.
        Args:
            prompt (str): The user's question.
        Returns:
            str: The LLM's off-topic assessment.
        """
        logger.info(f"Checking if prompt is medically pertinent: {prompt}")
        return self.query_extractor.check_medical_pertinence_query_ext_service(prompt)
        
    
    def check_chatbot_pertinence(self, prompt: str) -> str:
        """
        Determines if the user's question is relevant to the hospital ranking assistant.
        Args:
            prompt (str): The user's question.
        Returns:
            str: The LLM's assessment of relevance.
        """
        logger.info(f"Checking if prompt is chatbot pertinent: {prompt}")
        return self.query_extractor.check_chatbot_pertinence_query_ext_service(prompt)

    def detect_city(self, prompt: str) -> str:
        """
        Identifies the city or department mentioned in the user's question.
        Handles ambiguous cases with a two-step LLM process.
        Args:
            prompt (str): The user's question.
        Returns:
            str: The detected city or department.
        """
        logger.info(f"Detecting city in prompt: {prompt}")
        return self.query_extractor.detect_city_query_ext_service(prompt)

    def detect_topk(self, prompt: str):
        """
        Identifies if the number of institutions to display is mentioned in the user's question.
        Limits the number to a maximum of 50.
        Args:
            prompt (str): The user's question.
        Returns:
            int or str: The number of institutions to display, or 'non mentionné' if not specified or above 50.
        """
        logger.info(f"Detecting top_k in prompt: {prompt}")
        topk = self.query_extractor.detect_topk_query_ext_service(prompt)
        if topk != 'non mentionné':
            try:
                if int(topk) > 50:
                    topk = 'non mentionné'
                else:
                    topk = int(topk)
            except Exception:
                topk = 'non mentionné'
        return topk
        
    def detect_institution_type(self, prompt: str) -> str:
        """
        Determines if the user's question mentions a public or private institution, or a specific institution.
        Args:
            prompt (str): The user's question.
        Returns:
            str: The detected institution type or name.
        """
        logger.info(f"Checking if prompt mentions public or private institution: {prompt}")
        return self.query_extractor.detect_institution_type_query_ext_service(prompt)  

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
        return self.conversation_service.continue_conv_service(prompt, conv_history)

    def detect_modification(self, prompt: str, conv_history: list) -> str:
        """
        Detects if the user's new question is a modification of the last question or a new question.
        Args:
            prompt (str): The user's new question.
            conv_history (list): The conversation history.
        Returns:
            str: The LLM's response indicating whether it's a modification or a new question.
        """
        return self.conversation_service.detect_modification_conv_service(prompt, conv_history)
    
    def rewrite_query(self, last_query: str, modification: str) -> str:
        """
        Rewrites the last query based on the detected modification.
        Args:
            last_query (str): The last query made by the user.
            modification (str): The detected modification to the last query.
        Returns:
            str: The rewritten query based on the modification.
        """
        return self.conversation_service.rewrite_query_conv_service(last_query, modification)