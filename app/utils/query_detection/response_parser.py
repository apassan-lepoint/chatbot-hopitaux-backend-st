"""
Utility functions for parsing LLM responses into structured formats.
"""
from enum import Enum
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Response constants for better code readability
class CityResponse:
    NO_CITY_MENTIONED = 0
    FOREIGN = 1
    AMBIGUOUS = 2
    CITY_MENTIONED = 3


class ModificationResponse:
    NEW_QUESTION = 0
    MODIFICATION = 1
    AMBIGUOUS = 2

class SpecialtyResponse(Enum):
    NO_SPECIALTY_MENTIONED = 0
    SINGLE_SPECIALTY = 1
    MULTIPLE_SPECIALTIES = 2
    

def parse_boolean_response(response: str) -> bool:
    """Parse LLM response to boolean (1 = True, 0 = False)"""
    try:
        return int(response.strip()) == 1
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse boolean response: {response}")
        return False


def parse_numeric_response(response: str, default: int = 0) -> int:
    """Parse LLM response to integer"""
    try:
        return int(response.strip())
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse numeric response: {response}")
        return default


def parse_city_response(response: str) -> int:
    """Parse city detection response - returns numeric code"""
    try:
        code = int(response.strip())
        return code if code in [CityResponse.NO_CITY_MENTIONED, CityResponse.FOREIGN, CityResponse.AMBIGUOUS, CityResponse.CITY_MENTIONED] else CityResponse.NO_CITY_MENTIONED
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse city response: {response}")
        return CityResponse.NO_CITY_MENTIONED


def parse_modification_response(response: str) -> int:
    """Parse modification detection response - returns numeric code"""
    try:
        code = int(response.strip())
        return code if code in [ModificationResponse.NEW_QUESTION, ModificationResponse.MODIFICATION, ModificationResponse.AMBIGUOUS] else ModificationResponse.NEW_QUESTION
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse modification response: {response}")
        return ModificationResponse.NEW_QUESTION


def parse_institution_type_response(response: str) -> int:
    """Parse institution type response - returns numeric code"""
    try:
        response_int = int(response.strip())
        if response_int == 0:
            return "no match"
        elif response_int == 1:
            return "public"
        elif response_int == 2:
            return "private"
        else:
            logger.warning(f"Invalid institution type response: {response}")
            return "no match"
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse institution type response: {response}")
        return "no match"


def parse_specialty_response(response: str) -> SpecialtyResponse:
    """Parse specialty detection response to SpecialtyResponse enum."""
    try:
        response_int = int(response.strip())
        if response_int == 0:
            return SpecialtyResponse.NO_SPECIALTY_MENTIONED
        elif response_int == 1:
            return SpecialtyResponse.SINGLE_SPECIALTY
        elif response_int == 2:
            return SpecialtyResponse.MULTIPLE_SPECIALTIES
        else:
            return SpecialtyResponse.NO_SPECIALTY_MENTIONED
    except (ValueError, AttributeError):
        return SpecialtyResponse.NO_SPECIALTY_MENTIONED
    