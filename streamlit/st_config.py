"""
Config file for Streamlit application.
"""

## Session State constants 
# Make sure SESSION_STATE_KEYS is defined before SESSION_STATE_DEFAULTS
SESSION_STATE_KEYS = {
    "conversation": "conversation",
    "selected_option": "selected_option",
    "prompt": "prompt",
    "specialty": "specialty",
    "selected_specialty": "selected_specialty",
    "specialty_context": "specialty_context",
    "multiple_specialties": "multiple_specialties",
    "original_prompt": "original_prompt",
}

# Default values for Streamlit session state
SESSION_STATE_DEFAULTS = {
    SESSION_STATE_KEYS["conversation"]: [],
    SESSION_STATE_KEYS["selected_option"]: None,
    SESSION_STATE_KEYS["prompt"]: "",
    SESSION_STATE_KEYS["specialty"]: "",
    SESSION_STATE_KEYS["selected_specialty"]: None,
    SESSION_STATE_KEYS["specialty_context"]: None,
    SESSION_STATE_KEYS["multiple_specialties"]: None,
    SESSION_STATE_KEYS["original_prompt"]: "",
}


## Case Processing Messages 
CASE_MESSAGES = {
    "case1": "Message hors sujet détecté.",
    "case2": "Continuation avec fusion de requête détectée.",
    "case3": "Continuation avec ajout de requête détectée.",
    "case4": "Continuation LLM détectée.",
    "case5": "Nouvelle question avec recherche détectée.",
    "case6": "Nouvelle question LLM détectée."
}

## Checks to run 
DEFAULT_CHECKS_TO_RUN = [
    "message_length",
    "message_pertinence",
    "conversation_limit"
]

# Specialty match constant for normalization and logic
NO_SPECIALTY_MATCH = "no specialty match"

# Conversation Limits
MAX_MESSAGES = 5
MAX_MESSAGE_LENGTH = 1000  

## MESSAGES
# Spinner Messages 
SPINNER_MESSAGES = {
    "loading": "Chargement",
    "query_rewrite": "Réécriture de la requête",
    "processing": "Traitement en cours..."
}

# Off-topic Response
OFF_TOPIC_RESPONSE = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler une question relative aux classements des hôpitaux."

# Error Messages
ERROR_MESSAGES = {
    "general_processing": "Une erreur s'est produite lors du traitement de votre message.",
    "response_generation": "Erreur lors de la génération de la réponse.",
    "new_question_processing": "Erreur lors du traitement de votre nouvelle question.",
    "case_analysis": "Une erreur s'est produite lors de l'analyse de votre message. Veuillez réessayer.",
    "sanity_check_failed": "Erreur lors des vérifications de sécurité."
}


## UI Text Constants
UI_TITLE = "Assistant Hôpitaux"
UI_SUBTITLE = "Posez votre question ci-dessous."
UI_EXAMPLES_HEADER = "**Exemples de questions :**"
UI_NEW_CONVERSATION_BUTTON = "🔄 Démarrer une nouvelle conversation"
UI_SPECIALTY_SELECTION_PROMPT = "Précisez le domaine médical concerné :"
UI_CHAT_INPUT_PLACEHOLDER = "Votre message"
UI_INVALID_SELECTION_ERROR = "Sélection invalide. Veuillez choisir une option dans la liste."
EXAMPLE_QUESTIONS = ["Quel est le meilleur hôpital de Paris pour cancer de la vessie?",
                     "Où puis-je aller à Lille pour me faire soigner ?",
                     "Quels sont les 10 meilleurs hôpitaux publics à Bordeaux pour les maladies cardiaques ?"
                     ]

## CSS Styling 
BUTTON_CSS = """
<style>
/* Target all buttons in the main content area (not sidebar) */
.main .stButton > button:first-child {
    background-color: #E3F2FD !important;
    border: 1px solid #BBDEFB !important;
    color: #1976D2 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}
.main .stButton > button:first-child:hover {
    background-color: #BBDEFB !important;
    border: 1px solid #90CAF9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

/* Alternative selector targeting by button content */
button[kind="primary"] {
    background-color: #E3F2FD !important;
    border: 1px solid #BBDEFB !important;
    color: #1976D2 !important;
}
</style>
"""