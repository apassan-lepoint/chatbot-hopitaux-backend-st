# Lien vers le classement web du palmarès des hôpitaux
METHODOLOGY_WEB_LINK = "https://www.lepoint.fr/sante/la-methodologie-du-palmares-des-hopitaux-et-cliniques-du-point-2024--04-12-2024-2577146_40.php"
"""
Configuration constants for the chatbot hopitaux.
"""


# Default OpenAI model name
OPENAI_MODEL = "gpt-4o-mini"


# Ranking URLs and mapping 
PUBLIC_RANKING_URL = "https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-public.php"
PRIVATE_RANKING_URL = "https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-prive.php"
INSTITUTION_TYPE_URL_MAPPING = {
    "Public": "public",
    "Privé": "prive",
    "aucune correspondance": "aucune correspondance"
}

# User messages for different scenarios
OFF_TOPIC_RESPONSE = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler une question relative aux classements des hôpitaux."
INTERNAL_SERVER_ERROR_MSG = "Internal server error"
AMBIGUOUS_RESPONSE = "Je ne suis pas sûr si votre message est une nouvelle question ou une modification de la précédente. Veuillez préciser."
MESSAGE_LIMIT_REACHED_RESPONSE = "La limite de messages a été atteinte. La conversation va redémarrer."
MESSAGE_LENGTH_RESPONSE = "Votre message est trop long. Merci de reformuler."
FOREIGN_CITY_CHECK_EXCEPTION_MSG = "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
AMBIGUOUS_CITY_CHECK_EXCEPTION_MSG = "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
NO_PRIVATE_INSTITUTION_MSG = "Nous n'avons pas d'établissement privé pour cette pathologie, mais un classement des établissements publics existe."
NO_PUBLIC_INSTITUTION_MSG = "Nous n'avons pas d'établissement public pour cette pathologie, mais un classement des établissements privés existe."
NO_RESULTS_FOUND_IN_LOCATION_MSG = "Aucun résultat trouvé dans un rayon de 100 km autour de votre localisation."

WARNING_MESSAGES = {
    "message_length": "Votre message est trop long. Merci de le raccourcir.",
    "message_pertinence":"Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler.",
    "non_french_cities": "Je ne peux pas traiter les demandes concernant des villes étrangères. Merci de reformuler votre question en mentionnant une ville française.",
    "conversation_limit": "La conversation est trop longue. Merci de commencer une nouvelle conversation."
}  

# Error messages
ERROR_GENERAL_RANKING_MSG = "Erreur: Exception lors de la génération du classement général."
ERROR_INSTITUTION_RANKING_MSG = "Erreur: Exception lors de la récupération du classement de l'établissement."
ERROR_GEOPY_MSG = "Dû à une surutilisation de l'API de Geopy, le service de calcul des distances est indisponible pour le moment, merci de réessayer plus tard ou de recommencer avec une question sans localisation spécifique."
ERROR_DATA_UNAVAILABLE_MSG = "Erreur: Impossible de générer le classement car les données sont indisponibles."
ERROR_IN_CREATING_TABLE_MSG = "Erreur: Exception lors de la génération du classement."


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
MAX_MESSAGES = 0 # Keep as 0 for single=turn conversation
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


