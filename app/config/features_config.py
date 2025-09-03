"""
Configuration constants for the chatbot hopitaux.
"""


# Default OpenAI model name
OPENAI_MODEL = "gpt-4o-mini"

# Pricing and tracking settings
INPUT_PROMPT_PRICE_PER_TOKEN = 0.00000015  # $0.15 per 1M tokens
OUTPUT_COMPLETION_PRICE_PER_TOKEN = 0.00000060  # $0.60 per 1M tokens
TRACK_LLM_CALL_COST = True  # Enable or disable cost tracking

# Ranking URLs and mapping 
PUBLIC_RANKING_URL = "https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-public.php"
PRIVATE_RANKING_URL = "https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-prive.php"
INSTITUTION_TYPE_URL_MAPPING = {
    "Public": "public",
    "Privé": "prive",
    "aucune correspondance": "aucune correspondance"
}
METHODOLOGY_WEB_LINK = "https://www.lepoint.fr/sante/la-methodologie-du-palmares-des-hopitaux-et-cliniques-du-point-2024--04-12-2024-2577146_40.php"

# Non-error user messages
NON_ERROR_MESSAGES = {
    "multiple_specialties": "Plusieurs spécialités ont été détectées dans votre question. Merci de sélectionner une spécialité pour continuer.",
    "no_public_institution": "Nous n'avons pas d'établissement public pour cette pathologie, mais un classement des établissements privés existe.",
    "no_private_institution": "Nous n'avons pas d'établissement privé pour cette pathologie, mais un classement des établissements publics existe.",
    "no_results_found_in_location": "Aucun résultat trouvé dans un rayon de 100 km autour de votre localisation."
}


# Error user messages
ERROR_MESSAGES = {
    "message_length": "Votre message est trop long. Merci de le raccourcir.",
    "message_pertinence":"Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler une question relative aux classements des hôpitaux.",
    "non_french_cities": "Je ne peux pas traiter les demandes concernant des villes étrangères. Merci de reformuler votre question en mentionnant une ville française.",
    "conversation_limit": "La conversation est trop longue. Merci de commencer une nouvelle conversation.",
    "methodology_questions": "Les questions sur la méthodologie du classement sont hors périmètre du chatbot. Vous pouvez consulter la méthodologie complète <a href=\"{METHODOLOGY_WEB_LINK}\" target=\"_blank\">ici</a>.",
    "ambiguous_city": "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville.",
    "general_ranking_error": "Une erreur est survenue lors de la génération de votre réponse.",
    "institution_not_found": "Le nom de l'établissement que vous avez indiqué n'a pas été évalué dans le classement des hôpitaux. Merci de reformuler votre question.",
    "geopy_error": "Dû à une surutilisation de l'API de Geopy, le service de calcul des distances est indisponible pour le moment, merci de réessayer plus tard ou de recommencer avec une question sans localisation spécifique.",
    "general_error": "Je ne peux pas traiter votre demande. Merci de reformuler une question relative aux classements des hôpitaux.",
    "internal_server_error": "Internal server error."
}


# City related constants
CITY_NO_CITY_MENTIONED = 0
CITY_FOREIGN = 1
CITY_AMBIGUOUS = 2
CITY_MENTIONED = 3

# City status descriptions for better readability
STATUS_DESCRIPTIONS_DICT = {
    CITY_NO_CITY_MENTIONED: "No city mentioned",
    CITY_FOREIGN: "Foreign city detected",
    CITY_AMBIGUOUS: "Ambiguous city detection",
    CITY_MENTIONED: "French city mentioned"
    }


# Constants for checks
MAX_MESSAGES = 0 # Keep as 0 for single-turn conversation
MAX_LENGTH = 200
ENABLE_MULTI_TURN = False  # Set to False to disable multiturn logic



# Modification response constants
MODIFICATION_NEW_QUESTION = 0
MODIFICATION_MODIFICATION = 1
MODIFICATION_AMBIGUOUS = 2

# Specialty related constants
SPECIALTY_NO_SPECIALTY_MENTIONED = 0
SPECIALTY_SINGLE_SPECIALTY = 1
SPECIALTY_MULTIPLE_SPECIALTIES = 2


# Checks to run for sanity checks
CHECKS_TO_RUN_Q1 = ["message_length", "message_pertinence"]
CHECKS_TO_RUN_MULTI_TURN = ["message_length", "message_pertinence", "conversation_limit"]


# Number institution related constants
number_institutions_DEFAULT = 3
number_institutions_MIN = 1
number_institutions_MAX = 10


# Institution type relqted constants
INSTITUTION_TYPE_MAPPING = {
    "aucune correspondance": "aucune correspondance",
    "no match": "aucune correspondance",
    "public": "Public",
    "private": "Privé",
    "privé": "Privé",
    "prive": "Privé",
    "publique": "Public",
    "privée": "Privé"
}

INSTITUTION_TYPE_CODES = {
    "no_match": 0,
    "public": 1,
    "private": 2
}

# Search radius in kilometers
SEARCH_RADIUS_KM = [5, 10, 50, 100] 

# CSV Specific constants
CSV_FIELDNAMES = ['uuid', 'date', 'question', 'response', 'conversation_list', 'city', 'institution_type', 'institution_name', 'specialty', 'number_institutions', 'total_cost_sanity_checks', 'total_cost_query_analyst', 'total_cost_conversation_analyst', 'total_cost', 'total_tokens_sanity_checks', 'total_tokens_query_analyst', 'total_tokens_conversation_analyst', 'total_tokens']