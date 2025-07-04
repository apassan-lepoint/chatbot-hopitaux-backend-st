"""
This module provides a service for extracting queries using an LLM.
"""

from app.utils.query_detection.prompt_formatting import (
    format_second_detect_specialty_prompt,
    format_sanity_check_medical_pertinence_prompt,
    format_sanity_check_chatbot_pertinence_prompt,
    format_detect_city_prompt,
    format_second_detect_city_prompt,
    format_detect_topk_prompt,
    format_detect_institution_type_prompt,
    format_second_detect_institution_type_prompt
)
from app.utils.query_detection.response_parser import (
    parse_boolean_response, 
    parse_numeric_response,
    parse_city_response,
    parse_institution_type_response,
    CityResponse
)
from app.utils.query_detection.specialties import specialty_list
from app.utils.logging import get_logger
from app.utils.query_detection.institutions import institution_list, institution_coordinates_df

from app.utils.query_detection.specialties import specialty_categories_dict, extract_specialty_keywords
from app.utils.formatting import format_correspondance_list
from app.utils.llm_helpers import invoke_llm_with_error_handling, invoke_llm_and_parse_boolean

logger = get_logger(__name__)

class QueryExtractionService:
    """
    Service for extracting queries using a language model (LLM).
    This service handles the detection of medical specialties, medical pertinence, chatbot pertinence,
    city detection, top-k results, and institution types from user queries. 
    It uses the LLM to process prompts and extract relevant information based on predefined formats.
    
    Attributes:
        model: The LLM model to use for query extraction.
        key_words (optional): A dictionary of keywords to use for detecting specialties.
            If not provided, defaults to None.
        _institution_name: The name of the institution detected in the query.
        _institution_mentioned: A boolean indicating whether an institution was mentioned in the query. 
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

    def detect_specialty(self, prompt: str, specialty_list: list = specialty_list): 
        """
        Detects the medical specialty from the given prompt using the keyword mapping approach.
        Args:
            prompt (str): The input prompt containing the query.
            specialty_list (list): A list of specialties (kept for compatibility but not used).
        Returns:
            str: The detected specialty from the prompt.
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_second_detect_specialty_prompt(self.key_words, prompt)
        return invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_specialty")
        

    def detect_specialty_full(self, prompt: str) -> str:
        """
        Full specialty detection logic:
        1. Try LLM with keyword mapping approach.
        2. If ambiguous (multiple matches), clarify using specialty_categories_dict and extract_specialty_keywords.
        Always returns a string (never empty).
        """
        # Step 1: LLM with keyword mapping approach
        specialty = self.detect_specialty(prompt)

        # Step 2: If ambiguous (multiple matches), clarify using specialty_categories_dict
        if ',' in specialty and not specialty.startswith('multiple matches:'):
            specialty = 'multiple matches: ' + specialty

        if specialty.startswith("multiple matches:"):
            logger.info("Multiple specialties detected, clarifying with specialty_categories_dict")
            matches = extract_specialty_keywords(specialty, specialty_categories_dict)
            specialty = format_correspondance_list(matches)
            if not specialty or specialty.strip() == "":
                specialty = "no specialty match"
            return specialty

        # Step 3: If no match, we already used the keyword mapping approach in detect_specialty
        # No need for additional retry since detect_specialty now uses the keyword mapping
        if specialty == 'aucune correspondance' or not specialty or specialty.strip() == "":
            specialty = "no specialty match"
            
        return specialty
   
    
    def sanity_check_medical_pertinence(self, prompt, conv_history=""):
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Returns True if medically pertinent, False otherwise.
        
        Args:
            prompt: The message to check
            conv_history: Optional conversation history for context
        """
        formatted_prompt = format_sanity_check_medical_pertinence_prompt(prompt, conv_history)
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "sanity_check_medical_pertinence")

    def sanity_check_chatbot_pertinence(self, prompt, conv_history=""):
        """
        Checks the pertinence of the given prompt for the chatbot using the LLM.
        Returns True if relevant to chatbot, False otherwise.
        
        Args:
            prompt: The message to check
            conv_history: Optional conversation history for context
        """
        formatted_prompt = format_sanity_check_chatbot_pertinence_prompt(prompt, conv_history)
        return invoke_llm_and_parse_boolean(self.model, formatted_prompt, "sanity_check_chatbot_pertinence")

    def detect_city(self, prompt, conv_history=""):
        """
        Detects the city from the given prompt using the LLM.
        Returns: numeric code for status OR city name string if specific city found.
        - 0: no city mentioned
        - 1: foreign city
        - 2: ambiguous city  
        - 3: clear city mentioned
        - string: actual city name
        
        Args:
            prompt: The message to analyze
            conv_history: Optional conversation history for context
        """
        formatted_prompt = format_detect_city_prompt(prompt, conv_history)
        raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_city")
        city_status = parse_city_response(raw_response)
        
        # If a clear city is mentioned, retrieve the actual city name in a second LLM call
        if city_status == CityResponse.CITY_MENTIONED:
            formatted_prompt2 = format_second_detect_city_prompt(prompt, conv_history)
            city_name = invoke_llm_with_error_handling(self.model, formatted_prompt2, "detect_city (second call)")
            return city_name  # Return the actual city name
        
        return city_status  # Return the numeric status code


    def detect_topk(self, prompt):
        """
        Detects the top-k results from the given prompt using the LLM.
        Returns integer for top-k or 0 if not mentioned.
        """
        formatted_prompt = format_detect_topk_prompt(prompt)
        raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "get_topk")
        topk = parse_numeric_response(raw_response, 0)
        return topk if 1 <= topk <= 50 else 0
    
    
    @property
    def institution_name(self):
        return self._institution_name


    @property
    def institution_mentioned(self):
        return self._institution_mentioned

    
    def detect_institution_type(self, prompt: str, institution_list: str = institution_list):
        """
        Determines if the user's question mentions a public or private hospital, or none.
        Also detects if a specific institution is mentioned.
        """
        formatted_prompt = format_detect_institution_type_prompt(prompt, institution_list)
        institution_name = invoke_llm_with_error_handling(self.model, formatted_prompt, "is_public_or_private")
        logger.debug(f"LLM response: {institution_name}")
        
        # Check if the institution is in the list (split for robust matching)
        institution_names = [name.strip() for name in institution_list.split(",")]
        if institution_name in institution_names:
            self._institution_mentioned = True
            self._institution_name = institution_name
            logger.info(f"Institution mentioned: {institution_name}")
            institution_line = institution_coordinates_df[institution_coordinates_df['Etablissement'].str.contains(institution_name, case=False, na=False)]
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
            raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt2, "is_public_or_private (second call)")
            institution_type_code = parse_institution_type_response(raw_response)
            
            # Convert parsed response to expected string format for compatibility
            if institution_type_code == "public":
                institution_type = "Public"
            elif institution_type_code == "private":
                institution_type = "Privé"
            else:  # "no match"
                institution_type = "aucune correspondance"
                
            logger.debug(f"LLM response (second call): {raw_response}")
        
        return institution_type
