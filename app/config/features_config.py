# Constants for checks
MAX_MESSAGES = 5
MAX_LENGTH = 200




















# Response constants for better code readability
from enum import Enum

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
