"""
This module provides a service for extracting queries using an LLM.
"""

from app.utils.query_detection.prompt_formatting import (
    format_detect_specialty_prompt,
    format_second_detect_specialty_prompt,
    format_check_medical_pertinence_prompt,
    format_check_chatbot_pertinence_prompt,
    format_detect_city_prompt,
    format_second_detect_city_prompt,
    format_detect_topk_prompt,
    format_detect_institution_type_prompt,
    format_second_detect_institution_type_prompt
)
from app.utils.query_detection.specialties import specialties_list
from app.utils.logging import get_logger
from app.utils.query_detection.institutions import institution_list, coordinates_df

from app.utils.query_detection.specialties import specialty_categories_dict, extract_specialty_keywords
from app.utils.formatting import format_correspondance_list

logger = get_logger(__name__)

class QueryExtractionService:
    """
    Service for extracting queries using an LLM.
    """
    def __init__(self, model, key_words=None):
        """
        Initializes the QueryExtractionService with a model and optional keywords.
        Args:
            model: The LLM model to use for query extraction.
            key_words (optional): A dictionary of keywords to use for detecting specialties.
                If not provided, defaults to None.
        """
        self.model = model
        self.key_words = key_words
        self._institution_name = None
        self._institution_mentioned = False

    
    def detect_speciality(self, prompt: str, specialties_list: list = specialties_list): 
        """
        Detects the medical specialty from the given prompt using the provided specialties dictionary.
        Args:
            prompt (str): The input prompt containing the query.
            specialties_dict (dict): A dictionary mapping specialties to their names.
        Returns:
            str: The detected specialty from the prompt.
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_detect_specialty_prompt(specialties_list, prompt)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in get_speciality: {e}")
            raise
        return response.content.strip() if hasattr(response, "content") else str(response).strip()

    def detect_speciality_with_keywords(self, prompt: str):
        """
        Detects the medical specialty from the given prompt using the provided keywords.
        Args:
            prompt (str): The input prompt containing the query.    
        Returns:
            str: The detected specialty from the prompt.    
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_second_detect_specialty_prompt(self.key_words, prompt)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in get_speciality_with_keywords: {e}")
            raise
        return response.content.strip() if hasattr(response, "content") else str(response).strip()

    def detect_speciality_full_query_ext_service(self, prompt: str) -> str:
        """
        Full specialty detection logic:
        1. Try LLM with specialties_list.
        2. If ambiguous, clarify using specialty_categories_dict and extract_specialty_keywords.
        3. If no match, retry with keyword mapping.
        Always returns a string (never empty).
        """
        # Step 1: LLM with specialties_list
        specialty = self.detect_speciality(prompt)

        # Step 2: If ambiguous (multiple matches), clarify using specialty_categories_dict
        if ',' in specialty and not specialty.startswith('plusieurs correspondances:'):
            specialty = 'plusieurs correspondances: ' + specialty

        if specialty.startswith("plusieurs correspondances:"):
            logger.info("Multiple specialties detected, clarifying with specialty_categories_dict")
            matches = extract_specialty_keywords(specialty, specialty_categories_dict)
            specialty = format_correspondance_list(matches)
            if not specialty or specialty.strip() == "":
                specialty = "aucune correspondance"
            return specialty

        # Step 3: If no match, retry with keyword mapping
        if specialty == 'aucune correspondance' or not specialty or specialty.strip() == "":
            logger.info("No specialty match, retrying with keyword mapping")
            specialty = self.detect_speciality_with_keywords(prompt)
            if not specialty or specialty.strip() == "":
                specialty = "aucune correspondance"
            return specialty

        # Defensive: Always return a value
        if not specialty or specialty.strip() == "":
            specialty = "aucune correspondance"
        return specialty
    
    def check_medical_pertinence_query_ext_service(self, prompt):
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Args:
            prompt (str): The input prompt to check for medical pertinence.
        Returns:
            str: The response from the LLM indicating whether the prompt is medically pertinent.
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_check_medical_pertinence_prompt(prompt)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in check_medical_pertinence: {e}")
            raise
        return response.content.strip() if hasattr(response, "content") else str(response).strip()

    def check_chatbot_pertinence_query_ext_service(self, prompt):
        """
        Checks the pertinence of the given prompt for the chatbot using the LLM.
        Args:
            prompt (str): The input prompt to check for chatbot pertinence. 
        Returns:
            str: The response from the LLM indicating whether the prompt is pertinent for the chatbot.
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_check_chatbot_pertinence_prompt(prompt)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in check_chatbot_pertinence: {e}")
            raise
        return response.content.strip() if hasattr(response, "content") else str(response).strip()

    def detect_city_query_ext_service(self, prompt):
        """
        Detects the city from the given prompt using the LLM.
        Args:
            prompt (str): The input prompt containing the query.    
        Returns:
            str: The detected city from the prompt.
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_detect_city_prompt(prompt)
        try:
            response1 = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in detect_city: {e}")
            raise
        city = response1.content.strip() if hasattr(response1, "content") else str(response1).strip()
        
        # If there is no ambiguity, retrieve the city name in a second LLM call
        if city == 'correct':
            formatted_prompt2 = format_second_detect_city_prompt(prompt)
            try:
                response2 = self.model.invoke(formatted_prompt2)
            except Exception as e:
                logger.error(f"LLM invocation failed in detect_city (second call): {e}")
                raise
            city = response2.content.strip() if hasattr(response2, "content") else str(response2).strip()
        return city

    def detect_topk_query_ext_service(self, prompt):
        """
        Detects the top-k results from the given prompt using the LLM.
        Args:
            prompt (str): The input prompt containing the query.
        Returns:
            str: The top-k results detected from the prompt.
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_detect_topk_prompt(prompt)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in get_topk: {e}")
            raise
        topk = response.content.strip() if hasattr(response, "content") else str(response).strip()
        return topk
    
    @property
    def institution_name(self):
        return self.institution_name

    @property
    def institution_mentioned(self):
        return self.institution_mentioned
    
    def detect_institution_type_query_ext_service(self, prompt: str, institution_list: str = institution_list):
        """
        Determines if the user's question mentions a public or private hospital, or none.
        Also detects if a specific institution is mentioned.
        """
        formatted_prompt = format_detect_institution_type_prompt(prompt, institution_list)
        try:
            response1 = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in is_public_or_private: {e}")
            raise

        institution_name = response1.content.strip() if hasattr(response1, "content") else str(response1).strip()
        logger.debug(f"LLM response: {response1}")
        
        # Check if the institution is in the list (split for robust matching)
        institution_names = [name.strip() for name in institution_list.split(",")]
        if institution_name in institution_names:
            self.institution_mentioned = True
            self.institution_name = institution_name
            logger.info(f"Institution mentioned: {institution_name}")
            institution_line= coordinates_df[coordinates_df['Etablissement'].str.contains(institution_name, case=False, na=False)]
            if not institution_line.empty:
                institution_type = institution_line.iloc[0, 4]
            else:
                logger.warning(f"Institution '{institution_name}' not found in coordinates DataFrame.")
                institution_type = "unknown"
        else:
            self._institution_mentioned = False
            self._institution_name = None
            logger.info("No institution detected, checking for public/private criterion")
            formatted_prompt2 = format_second_detect_institution_type_prompt(prompt)
            try:
                response2 = self.model.invoke(formatted_prompt2)
            except Exception as e:
                logger.error(f"LLM invocation failed in is_public_or_private (second call): {e}")
                raise
            institution_type = response2.content.strip() if hasattr(response2, "content") else str(response2).strip()
            logger.debug(f"LLM response (second call): {response2}")
        return institution_type
    
   