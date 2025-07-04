"""
This module contains prompt templates for interacting with the LLM.

Each prompt is designed for a specific task: identifying medical specialties,
detecting off-topic questions, extracting city names, or continuing conversations.

The prompts use placeholders (e.g., {prompt}, {specialty_list}) to be filled dynamically
at runtime.

Attributes:
    PROMPT_INSTRUCTIONS (dict[str, str]): 
        Keys: Names of the prompts.
        Values: Template strings for each prompt.
"""

from typing import Dict

# Prompt templates for LLM interactions
PROMPT_INSTRUCTIONS: Dict[str, str] = {
    "detect_specialty_prompt": """
Voici un message pour lequel tu vas devoir choisir la spécialité qui correspond le plus. 
Voici mon message : {prompt}.

Voici une liste de spécialité pour laquelle tu vas devoir choisir la spécialité qui correspond le plus à mon message : 
liste des spécialités: '{specialty_list}'. 

N'invente pas de spécialité qui n'est pas dans la liste. 

Analysez le message de l'utilisateur et déterminez si une ou plusieurs spécialités médicales dans la liste des spécialités sont mentionnées:
0 - Aucune spécialité médicale mentionnée
1 - Une spécialité médicale mentionnée
2 - Plusieurs spécialités médicales mentionnées

Exemples: 
Pour le message 'Quel est le meilleur hôpital privé à Paris?', tu me répondras 0.
Pour le message 'Quels sont les trois meilleurs hôpitaux en France', tu me répondras 0.
Pour le message 'Quel est le meilleur hôpital d'audition?', tu me répondras 1.
Pour le message 'Je veux soigner mon AVC?', tu me répondras 1.
Pour le message 'Je cherche un hôpital pour un accouchement', tu me répondras 2.
Pour le message 'J'ai mal au genou', tu me répondras 2.
""",

    "second_detect_specialty_prompt": """
Voici un message pour lequel tu vas devoir trouver la ou les pathologie(s) qui correspondent le plus: '{prompt}'
Voici la liste des pathologies et des mots clés associés pour t'aider: {mapping_words}

Si une seule spécialité de la liste correspond à ma demande, réponds UNIQUEMENT avec la spécialité exacte de la liste. 
Exemple: Pour le message 'Je veux soigner mon AVC?', tu me répondras 'Accidents vasculaires cérébraux'.

Si plusieurs spécialités de la liste peuvent correspondre ou sont liées au message, réponds UNIQUEMENT avec les spécialités exactes de la liste et sous le format suivant: 'plusieurs correspondances: spécialité 1, spécialité 2'.
Exemple: pour le message 'Je cherche un hôpital pour un accouchement', tu me répondras 'plusieurs correspondances: Accouchements à risques, Accouchements normaux'.
Exemple: pour le message 'J'ai mal au genou', tu me répondras 'plusieurs correspondances: Prothèse de genou, Ligaments du genou'.

Si aucune spécialité de la liste est liée à ma demande, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'
N'invente pas de spécialité qui n'est pas dans la liste
""",

    "sanity_check_medical_pertinence_prompt": """
Évaluez si le message suivant a un rapport avec la santé humaine ou les services de soins: '{prompt}'
Répondez UNIQUEMENT avec 1 si pertinent, 0 si non pertinent.

Exemples : 
Par exemple pour le message: 'J'ai un cancer à Paris', tu retourneras: 1.
Par exemple pour le message: 'Cataracte', tu retourneras: 1.
Par exemple pour le message: 'J'ai mal aux pieds', tu retourneras: 1.
Par exemple pour le message: 'Les hôpitaux privés sont ils meilleurs que les publiques?', tu retourneras: 1.
Par exemple pour le message: 'Je mange des frites', tu retourneras: 0.
""",

    "sanity_check_chatbot_pertinence_prompt": """
Vérifiez si cette question concerne le classement des hôpitaux: '{prompt}'
Répondez UNIQUEMENT avec 1 si pertinent, 0 si non pertinent.

Une question est pertinente si elle concerne au moins un des cas suivants:
- Une maladie, un symptôme ou une spécialité médicale  
- Le classement des hôpitaux et cliniques  
- La recherche d'un hôpital, d'une clinique ou d'un service médical  

Exemples de questions pertinentes (repondre 1) :  
- Quel est la meilleur clinique de France ?
- Conseille moi un hôpital à Lyon 
- Je chercher un service de pneumologie
- Où faire soigner mon glaucome ? 
- Je veux corriger mon audition
- Il y a fréquemment du sang dans mes urines. Conseille-moi un hôpital. 
- Je veux cherche à faire soigner mes troubles bipôlaires
- Est-ce que l'Institut mutualiste Montsouris est bon ?
- Y a-t-il des hôpitaux privés avec un service de cardiologie interventionnelle ?

Exemples de questions non pertinentes (repondre 0) :  
- Pourquoi les hôpitaux sont-ils en crise ?  #Il s'agit d'une demande d'information qui n'est pas dans le cadre direct de la recherche d'un établissement de soin
- Dois-je prendre du paracétamol pour ma fièvre ? #Il s'agit d'une demande d'expertise médical qui n'est pas dans le cadre de la recherche d'un établissement de soin
- Puis-je perdre la vue si j'ai un glaucome? #Il s'agit d'une demande d'expertise médical qui n'est pas dans le cadre de la recherche d'un établissement de soin
""",

    "detect_city_prompt": """
Analysez cette phrase pour détecter des informations de localisation: '{prompt}'
Répondez avec:
- 0 si aucune localisation n'est mentionnée
- 1 si ville étrangère  
- 2 si confusion entre villes françaises
- 3 si une ville ou localisation française claire est mentionnée
""",

    "second_detect_city_prompt": """
Quelle ville ou département est mentionné par la phrase suivante : '{prompt}'?
Si une ville est mentionnée, réponds UNIQUEMENT avec le nom de ville.
Par exemple:  pour la phrase, 'Trouve moi un hôpital à Lyon', tu me retourneras: 'Lyon'.

Si un département est mentionné, réponds UNIQUEMENT avec le numéro du département.
Par exemple:  pour la phrase, 'Je veux être hospitalisé dans le 92', tu me retourneras: '92'.               

Si aucune localisation n'est mentionnée dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'.
Par exemple:  pour la phrase, 'Je veux un classement des meilleurs établissements en France', tu me retourneras: 'aucune correspondance'.
Par exemple:  pour la phrase, 'Quelle est la meilleur clinique pour une chirurgie à la montagne', tu me retourneras: 'aucune correspondance'.
""",

    "detect_topk_prompt": """
Extrayez le nombre d'établissements demandés dans: '{prompt}'
Répondez UNIQUEMENT avec le nombre (1-50) ou 0 si non mentionné.

Par exemple: pour la phrase 'Quels sont les trois meilleurs hôpitaux pour soigner mon audition ?', tu me retourneras: '3'.

Si la phrase inclue une expression comme 'le plus xxx' ou du superlatif qui implique implicitement une seule entité comme 'le meilleur', alors tu me retourneras '1'
Par exemple: pour la phrase 'Quel est la meilleur clinique de Nantes?' ou 'Dis moi l'établissement le plus populaire de France' tu me retourneras: '1'.
""",

    "detect_institution_type_prompt": """
Un des noms exact de ma liste d'établissements est il mentionné précisément dans cette phrase: '{prompt}'? Voici ma liste d'établissements:
{institution_list}
Réponds UNIQUEMENT avec le nom d'établissement exact de la liste si la phrase contient un des noms exacts d'établissement.
Si aucun de ces établissement n'est mentionné dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'.
Si la Ville de l'établissement est mentionnée mais pas le nom complet, par exemple 'Villeneuve-d'Ascq' est mentionné mais pas 'Clinique de Villeneuve-d'Ascq' alors tu renverras 'aucune correspondance'. 

Voici des exemples sans noms d'établissement: pour la phrase 'Je cherche un hôpital pour soigner mon audition à Toulon ?' ou 'Quelle est la meilleure clinique de Limoges?', tu me répondras 'aucune correspondance'.
Voici un exemple avec noms d'établissement: pour la phrase 'Est-ce que l'Hôpital Edouard-Herriot est bon en cas de problèmes auditifs ?' tu me répondras 'Hôpital Edouard-Herriot'. 
""",

    "second_detect_institution_type_prompt": """
Détectez le type d'établissement de soin dans: '{prompt}'
Répondez UNIQUEMENT avec:
- 0 si aucun type mentionné
- 1 si public
- 2 si privé
""",

    "continue_conversation_prompt": """
Vous êtes un assistant intelligent. Voici l'historique de la conversation précédente entre l'utilisateur et vous :{conv_history}
Réponds au nouveau message de l'utilisateur:{prompt}
""",
        
    "detect_modification_prompt": """
Analysez si ce message modifie la question précédente en gardant le même contexte (lieu, spécialité, etc.):

Historique: {conv_history}
Nouveau message: {prompt}

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
        
    "rewrite_query_prompt": """
Voici la question initiale de l'utilisateur :
{last_query}

Voici la modification ou précision apportée par l'utilisateur :
{modification}

Reformule une nouvelle question complète et précise qui prend en compte la modification.
""",

    "continuity_check_prompt": """
Analysez si ce nouveau message est une continuation de la conversation précédente:
Historique: {conv_history}
Nouveau message: {prompt}

Répondez UNIQUEMENT avec:
- 1 si c'est une continuation de la conversation
- 0 si c'est une nouvelle question indépendante
""",

    "search_needed_check_prompt": """
Déterminez si cette question nécessite une recherche dans les données de classement des hôpitaux: '{prompt}'
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
""",

    "merge_query_check_prompt": """
Analysez comment combiner cette nouvelle demande avec la conversation précédente:
Historique: {conv_history}
Nouveau message: {prompt}

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

Historique: {conv_history}
Nouveau message: {prompt}

Reformulez en une question complète et précise:
""",

    "add_query_rewrite_prompt": """
Créez une nouvelle question en ajoutant les filtres du nouveau message à ceux de l'historique.

Historique: {conv_history}
Nouveau message: {prompt}

Reformulez en une question complète et précise qui combine tous les critères:
"""
}
