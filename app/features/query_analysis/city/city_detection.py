from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import parse_llm_response, prompt_formatting
from app.config.features_config import CITY_MENTIONED, CITY_FOREIGN, CITY_AMBIGUOUS, CITY_NO_CITY_MENTIONED, STATUS_DESCRIPTIONS_DICT

logger = get_logger(__name__)

class CityDetector:
    """
    Service for detecting cities mentioned in user queries.
    
    This class handles the detection of cities or locations mentioned by users,
    including validation for French cities, foreign cities, and ambiguous cases.
    It supports conversation history context for better detection accuracy.

    Attributes:
        model: The language model used for city detection.  
    Methods:
        detect_city(prompt: str, conv_history: str = "") -> str:
            Detects the city from the given prompt using the LLM.
        _detect_city_status(prompt: str, conv_history: str = "") -> int:
            Detects the status of city detection from the given prompt.
        _detect_city_name(prompt: str, conv_history: str = "") -> str:
            Detects the city name from the given prompt using the LLM.
        _get_city_response_description(city_status: int) -> str:
            Gets a human-readable description of the city response based on its status. 
    """
    
    def __init__(self, model):
        logger.info("Initializing CityDetector")
        self.model = model
    
    def _detect_city_status(self, prompt: str, conv_history: str = "") -> int:
        """
        Detects the status of city detection from the given prompt using the LLM.
        This method determines if a city is mentioned, foreign, ambiguous, or not mentioned at all.
        """
        logger.debug(f"_detect_city_status called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting("detect_city_prompt", prompt=prompt, conv_history=conv_history)
        raw_response = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_city_status"
        )
        logger.info(f"Raw LLM response for city status: {raw_response}")
        city_status = parse_llm_response(raw_response, "city")
        logger.info(f"Parsed city status: {city_status}")
        return city_status
    
    def _detect_city_name(self, prompt: str, conv_history: str = "") -> str:
        """
        Detects the city name from the given prompt using the LLM.
        """
        logger.debug(f"_detect_city_name called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting("second_detect_city_prompt", prompt=prompt, conv_history=conv_history)
        city_name = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_city_name"
        )
        logger.info(f"Raw LLM response for city name: {city_name}")
        logger.debug(f"City name extracted: {city_name}")
        return city_name.strip()
    

    def _get_city_response_description(self, city_status) -> str:
        """
        Gets a human-readable description of the city response.
        """
        if isinstance(city_status, str):
            return f"French city: {city_status}"
        return STATUS_DESCRIPTIONS_DICT.get(city_status, f"Unknown status: {city_status}")

    def detect_city(self, prompt: str, conv_history: str = ""):
        logger.debug(f"detect_city called: prompt={prompt}, conv_history={conv_history}")
        """
        Detects the city from the given prompt using the LLM.
        
        This is the main method for city detection. It first determines the status
        of city detection (no city, foreign, ambiguous, or mentioned), and if a
        city is clearly mentioned, it makes a second call to extract the actual
        city name.
        """
        logger.info(f"Detecting city from prompt: '{prompt}'")
        
        # First call: detect city status
        city_status = self._detect_city_status(prompt, conv_history)
        
        # If a clear city is mentioned, retrieve the actual city name
        if city_status == CITY_MENTIONED:
            logger.debug("City mentioned detected, extracting city name")
            city_name = self._detect_city_name(prompt, conv_history)
            logger.info(f"City detected: {city_name}")
            # Defensive: ensure city_name is valid
            if not city_name or not isinstance(city_name, str) or city_name.strip() == "":
                logger.warning("City name extraction failed, returning CITY_NO_CITY_MENTIONED status code")
                return CITY_NO_CITY_MENTIONED
            return city_name.strip()
        # Defensive: always return a proper status code, never a string error
        if not isinstance(city_status, int) or city_status not in [CITY_NO_CITY_MENTIONED, CITY_FOREIGN, CITY_AMBIGUOUS, CITY_MENTIONED]:
            logger.warning(f"Invalid city status detected: {city_status}, returning CITY_NO_CITY_MENTIONED")
            return CITY_NO_CITY_MENTIONED
        logger.info(f"City detection status: {self._get_city_response_description(city_status)}")
        return city_status
    
    
    def get_city_status_type(self, city_status):
        """
        Returns a string representing the type of city status.
        """
        if city_status == CITY_MENTIONED or isinstance(city_status, str):
            return "french"
        elif city_status == CITY_FOREIGN:
            return "foreign"
        elif city_status == CITY_AMBIGUOUS:
            return "ambiguous"
        elif city_status == CITY_NO_CITY_MENTIONED:
            return "none"
        else:
            return "unknown"


