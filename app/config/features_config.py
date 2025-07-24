# Constants for checks
MAX_MESSAGES = 5
MAX_LENGTH = 200

# Response constants for better code readability

# City response constants
CITY_NO_CITY_MENTIONED = 0
CITY_FOREIGN = 1
CITY_AMBIGUOUS = 2
CITY_MENTIONED = 3

# Modification response constants
MODIFICATION_NEW_QUESTION = 0
MODIFICATION_MODIFICATION = 1
MODIFICATION_AMBIGUOUS = 2

# Specialty response constants
SPECIALTY_NO_SPECIALTY_MENTIONED = 0
SPECIALTY_SINGLE_SPECIALTY = 1
SPECIALTY_MULTIPLE_SPECIALTIES = 2

AMBIGUOUS_RESPONSE = "Je ne suis pas sûr si votre message est une nouvelle question ou une modification de la précédente. Veuillez préciser."

# Checks to run for sanity checks
CHECKS_TO_RUN_Q1 = ["message_length", "message_pertinence"]
CHECKS_TO_RUN_MULTI_TURN = ["message_length", "message_pertinence", "conversation_limit"]


# Warning messages for different checks
WARNING_MESSAGES = {
    "message_length": "Votre message est trop long. Merci de le raccourcir.",
    "message_pertinence":"Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler.",
    "non_french_cities": "Je ne peux pas traiter les demandes concernant des villes étrangères. Merci de reformuler votre question en mentionnant une ville française.",
    "conversation_limit": "La conversation est trop longue. Merci de commencer une nouvelle conversation."
}   

# TopK response constants
TOPK_DEFAULT = 3
TOPK_MIN = 1
TOPK_MAX = 10
