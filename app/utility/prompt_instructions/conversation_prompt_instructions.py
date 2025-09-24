"""
Prompt instructions for managing conversation context and queries in a chatbot.
"""

from typing import Dict

# Prompt templates for LLM interactions
CONVERSATION_PROMPT_INSTRUCTIONS: Dict[str, str] = {

    "continue_conversation_prompt": """
Vous êtes un assistant intelligent. 

HISTORIQUE DE CONVERSATION:
{conv_history}

NOUVEAU MESSAGE DE L'UTILISATEUR: {prompt}

Réponds au nouveau message de l'utilisateur en tenant compte de l'historique de conversation.
""",
        
    "detect_modification_prompt": """
Analysez si ce message modifie la question précédente en gardant le même contexte (lieu, spécialité, etc.):

HISTORIQUE DE CONVERSATION:
{conv_history}

NOUVEAU MESSAGE: {prompt}

EXEMPLES de modifications (retourner 1):
- "et privé ?" → modifie le type d'hôpital
- "et public ?" → modifie le type d'hôpital  
- "pour neurologie ?" → modifie la spécialité
- "à Lyon ?" → modifie la ville
- "orthopédie ?" → remplace la spécialité
- Questions très courtes qui font référence au contexte précédent

EXEMPLES de nouvelles questions (retourner 0):
- Questions complètes avec lieu ET spécialité
- Questions sur un sujet complètement différent
- Questions générales sur le système

Répondez UNIQUEMENT avec:
- 0 pour nouvelle question
- 1 pour modification de la question précédente
- 2 pour ambiguous
""",

    "continuity_check_prompt": """
Analysez si ce nouveau message est une continuation de la conversation précédente:

HISTORIQUE DE CONVERSATION:
{conv_history}

NOUVEAU MESSAGE: {prompt}

Répondez UNIQUEMENT avec:
- 1 si c'est une continuation de la conversation
- 0 si c'est une nouvelle question indépendante
""",

    "search_needed_check_prompt": """
Déterminez si cette question nécessite une recherche dans les données de classement des hôpitaux.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Une recherche peut être nécessaire même pour des messages courts si le contexte indique une demande de données hospitalières.

Répondez UNIQUEMENT avec 1 si une recherche est nécessaire, 0 sinon.

Une recherche est nécessaire si la question demande:
- Des recommandations d'hôpitaux spécifiques
- Des classements ou comparaisons d'établissements
- Des informations sur les meilleurs hôpitaux pour une spécialité
- Des données factuelles sur les performances hospitalières

Une recherche N'EST PAS nécessaire pour:
- Des questions générales sur la santé
- Des demandes d'explications sur les réponses précédentes
- Des clarifications ou reformulations
- Des remerciements simples

Exemples avec contexte conversationnel:
- Avec historique sur la recherche d'hôpitaux, 'et privé?' → 1 (modification de critères de recherche)
- Avec historique sur classements, 'Merci pour ces informations' → 0 (remerciement simple)
- Avec historique général, 'les meilleurs à Lyon' → 1 (nouvelle demande de recherche)
""",

    "merge_query_check_prompt": """
Analysez comment combiner cette nouvelle demande avec la conversation précédente:

HISTORIQUE DE CONVERSATION:
{conv_history}

NOUVEAU MESSAGE: {prompt}

Répondez UNIQUEMENT avec:
- 1 si les filtres du nouveau message doivent REMPLACER ceux de la conversation précédente
- 0 si les filtres du nouveau message doivent s'AJOUTER à ceux de la conversation précédente

Exemples:
- "Et à Lyon maintenant?" -> 1 (remplace la ville)
- "Aussi pour les enfants" -> 0 (ajoute une spécialité)
""",

    "merge_query_rewrite_prompt": """
Créez une nouvelle question en fusionnant l'historique et le nouveau message.
Les filtres du nouveau message remplacent ceux conflictuels de l'historique.

HISTORIQUE DE CONVERSATION:
{conv_history}

NOUVEAU MESSAGE: {prompt}

Reformulez en une question complète et précise:
""",

    "add_query_rewrite_prompt": """
Créez une nouvelle question en ajoutant les filtres du nouveau message à ceux de l'historique.

HISTORIQUE DE CONVERSATION:
{conv_history}

NOUVEAU MESSAGE: {prompt}

Reformulez en une question complète et précise qui combine tous les critères.
"""
}