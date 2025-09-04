"""
This module contains prompt templates for interacting with the LLM.

Each prompt is designed for a specific task: identifying medical specialties,
detecting off-topic questions, extracting city names, or continuing conversations.

The prompts use placeholders (e.g., {prompt}, {specialty_list}) to be filled dynamically
at runtime.
"""

from typing import Dict

# Prompt templates for LLM interactions
PROMPT_INSTRUCTIONS: Dict[str, str] = {
    "detect_specialty_prompt": """
Voici un message pour lequel tu vas devoir choisir la spécialité qui correspond le plus.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: {prompt}

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Une spécialité peut être mentionnée de manière implicite si le contexte de la conversation montre qu'on parle d'une spécialité spécifique.

Voici une liste de spécialité pour laquelle tu vas devoir choisir la spécialité qui correspond le plus à mon message : 
liste des spécialités: '{specialty_list}'. 

N'invente pas de spécialité qui n'est pas dans la liste. 

Analysez le message de l'utilisateur et déterminez si une ou plusieurs spécialités médicales dans la liste des spécialités sont mentionnées:
0 - Aucune spécialité médicale mentionnée
1 - Une spécialité médicale mentionnée
2 - Plusieurs spécialités médicales mentionnées

Exemples pour messages standalone: 
Pour le message 'Quel est le meilleur hôpital privé à Paris?', tu me répondras 0.
Pour le message 'Quels sont les trois meilleurs hôpitaux en France', tu me répondras 0.
Pour le message 'Quel est le meilleur hôpital d'audition?', tu me répondras 1.
Pour le message 'Je veux soigner mon AVC?', tu me répondras 1.
Pour le message 'Je cherche un hôpital pour un accouchement', tu me répondras 2.
Pour le message 'J'ai mal au genou', tu me répondras 2.

Exemples avec contexte conversationnel:
- Avec historique sur la cardiologie, 'et privé?' → 1 (la spécialité cardiologie est implicitement mentionnée)
- Avec historique sur plusieurs spécialités, 'pour les enfants' → 2 (peut référer à plusieurs spécialités pédiatriques)
- Avec historique général, 'orthopédie' → 1 (spécialité explicitement mentionnée)
""",

    "second_detect_specialty_prompt": """
Voici un message pour lequel tu vas devoir trouver la ou les pathologie(s) qui correspondent le plus.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Une spécialité peut être mentionnée de manière implicite si le contexte de la conversation montre qu'on parle d'une spécialité spécifique.

Voici la liste des pathologies et des mots clés associés pour t'aider: {mapping_words}

Si une seule spécialité de la liste correspond à ma demande, réponds UNIQUEMENT avec la spécialité exacte de la liste. 
Exemple: Pour le message 'Je veux soigner mon AVC?', tu me répondras 'Accidents vasculaires cérébraux'.

Si plusieurs spécialités de la liste peuvent correspondre ou sont liées au message, réponds UNIQUEMENT avec les spécialités exactes de la liste et sous le format suivant: 'plusieurs correspondances: spécialité 1, spécialité 2'.
Exemple: pour le message 'Je cherche un hôpital pour un accouchement', tu me répondras 'plusieurs correspondances: Accouchements à risques, Accouchements normaux'.
Exemple: pour le message 'J'ai mal au genou', tu me répondras 'plusieurs correspondances: Prothèse de genou, Ligaments du genou'.

Si aucune spécialité de la liste est liée à ma demande, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'

ATTENTION: Soyez attentif aux problèmes digestifs et gastro-intestinaux. Les termes comme 'gastro-entérite', 'diarrhée', 'vomissements', 'maux de ventre', 'troubles digestifs' peuvent correspondre à des spécialités comme 'Proctologie', 'Maladies inflammatoires chroniques de l'intestin (MICI)', ou autres spécialités digestives de la liste.

Exemples spécifiques:
- 'J'ai une gastro-entérite' → 'Proctologie' (si cette spécialité existe dans la liste)
- 'J'ai des troubles digestifs' → 'Maladies inflammatoires chroniques de l'intestin (MICI)' (si cette spécialité existe dans la liste)
- 'J'ai mal au ventre' → 'Proctologie' (si cette spécialité existe dans la liste)

Exemples avec contexte conversationnel:
- Avec historique sur la cardiologie, 'et privé?' → 'Cardiologie interventionnelle' (si cette spécialité existe dans la liste)
- Avec historique sur plusieurs spécialités du genou, 'pour les enfants' → 'plusieurs correspondances: Orthopédie pédiatrique, Prothèse de genou' (si ces spécialités existent)

N'invente pas de spécialité qui n'est pas dans la liste
""",

    "sanity_check_medical_pertinence_prompt": """
Évaluez si le message suivant a un rapport avec la santé humaine ou les services de soins.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ÉVALUER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Un message peut être pertinent même s'il semble incomplet ou ambigu, si le contexte de la conversation montre qu'il s'agit d'une suite logique d'une discussion sur la santé.

ATTENTION: Les questions de suivi sur les hôpitaux publics/privés sont TOUJOURS pertinentes. Les mots comme "privé", "public", "et privé?", "et public?" dans le contexte d'une discussion sur les hôpitaux sont des continuations légitimes de discussions médicales.
ATTENTION: Toute question sur la méthodologie, la fréquence de mise à jour, les critères, ou le fonctionnement du classement des hôpitaux doit TOUJOURS être considérée comme pertinente, même si elle ne concerne pas directement une maladie ou un service de soins.

Répondez UNIQUEMENT avec 1 si pertinent, 0 si non pertinent ou 2 si la question concerne la méthodologie de calcul du classement.

Exemples pour messages standalone (repondre 1): 
- 'J'ai un cancer à Paris' → 1
- 'Cataracte' → 1  
- 'J'ai mal aux pieds' → 1
- 'Les hôpitaux privés sont ils meilleurs que les publiques?' → 1
- 'Comment le classement est-il calculé ?' → 1
- 'Quels sont les critères du classement ?' → 1
- "Quels experts participent à l'élaboration du classement ?"' → 1
- "Le classement est-il influencé par des partenariats ou des sponsors ?"' → 1
- "Comment sont traitées les données manquantes dans le classement ?"' → 1
- "Le classement est-il le même pour toutes les spécialités ?"' → 1
- "Comment sont comparés les hôpitaux publics et privés dans le classement ?"' → 1
- "Quels sont les changements dans la méthodologie cette année ?"' → 1
- "Comment puis-je accéder au détail de la méthodologie ?"' → 1

Exemples pour messages standalone (repondre 0):
- 'Je mange des frites' → 0
- 'Comment faire une tarte aux pommes ?' → 0
- 'Comment s'abonner Le Point ?' → 0
- 'Quel est le meilleur restaurant à Paris ?' → 0


Exemples de questions qui concernent la méthodologie de classement (repondre 2):
- "Comment le classement est-il calculé ?"
- "Quels sont les critères du classement ?" 
- "Pourquoi l'hôpital X est mieux classé que Y ?"
- "Comment sont choisis les critères du classement ?"
- "Qui réalise le classement des hôpitaux ?"
- "Quelle est la source des données utilisées pour le classement ?"
- "Le classement prend-il en compte la satisfaction des patients ?"
- "Comment sont pondérés les différents critères ?"
- "Est-ce que le classement est mis à jour chaque année ?"
- "Pourquoi certains hôpitaux ne figurent pas dans le classement ?"
- "Comment puis-je vérifier la fiabilité du classement ?"
- "Quels experts participent à l'élaboration du classement ?"
- "Le classement est-il influencé par des partenariats ou des sponsors ?"
- "Comment sont traitées les données manquantes dans le classement ?"
- "Le classement est-il le même pour toutes les spécialités ?"
- "Comment sont comparés les hôpitaux publics et privés dans le classement ?"
- "Quels sont les changements dans la méthodologie cette année ?"
- "Comment puis-je accéder au détail de la méthodologie ?"

Exemples pour messages avec contexte conversationnel (TRÈS IMPORTANT):
- Avec historique montrant une discussion sur les hôpitaux, 'Et à Lyon ?' → 1 (question de suivi sur les hôpitaux)
- Avec historique sur la cardiologie, 'Merci' → 1 (remerciement dans contexte médical)
- Avec historique sur hôpitaux publics, 'et privé?' → 1 (question de suivi sur le secteur privé)
- Avec historique sur hôpitaux privés, 'et public?' → 1 (question de suivi sur le secteur public)
- Avec historique sur cardiologie publique, 'privé?' → 1 (question de suivi sur le secteur privé)
- Avec historique mentionnant "privés", 'et privé?' → 1 (demande de précision sur le secteur privé)
- Avec historique sur hôpitaux de Bordeaux, 'publics aussi?' → 1 (question de suivi sur le secteur public)
- Même avec contexte médical, 'Parle-moi de football' → 0 (hors-sujet)
- Avec historique sur les classements, "Comment sont déterminés les scores ?" → 2 (question sur la méthodologie de classement)
""",

    "sanity_check_chatbot_pertinence_prompt": """
Vérifiez si cette question concerne le classement des hôpitaux.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ÉVALUER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Un message peut être pertinent même s'il semble incomplet ou ambigu, si le contexte de la conversation montre qu'il s'agit d'une suite logique d'une discussion sur les classements d'hôpitaux.

ATTENTION: Les questions de suivi sur les hôpitaux publics/privés sont TOUJOURS pertinentes. Les mots comme "privé", "public", "et privé?", "et public?" dans le contexte d'une discussion sur les hôpitaux sont des continuations légitimes.

Répondez UNIQUEMENT avec:
- 1 si la question est pertinente pour le chatbot (classement, recherche d'établissement, etc.)
- 0 si la question n'est pas pertinente

Une question est pertinente si elle concerne au moins un des cas suivants:
- Une maladie, un symptôme ou une spécialité médicale  
- Le classement des hôpitaux et cliniques  
- La recherche d'un hôpital, d'une clinique ou d'un service médical  
- Une question de suivi sur les secteurs public/privé des hôpitaux

Exemples de questions pertinentes pour messages standalone (repondre 1):  
- Quel est la meilleur clinique de France ?
- Conseille moi un hôpital à Lyon 
- Je chercher un service de pneumologie
- Où faire soigner mon glaucome ? 
- Je veux corriger mon audition
- Il y a fréquemment du sang dans mes urines. Conseille-moi un hôpital. 
- Je veux cherche à faire soigner mes troubles bipôlaires
- Est-ce que l'Institut mutualiste Montsouris est bon ?
- Y a-t-il des hôpitaux privés avec un service de cardiologie interventionnelle ?

Exemples de questions non pertinentes pour messages standalone (repondre 0):  
- Pourquoi les hôpitaux sont-ils en crise ?  #Il s'agit d'une demande d'information qui n'est pas dans le cadre direct de la recherche d'un établissement de soin
- Dois-je prendre du paracétamol pour ma fièvre ? #Il s'agit d'une demande d'expertise médical qui n'est pas dans le cadre de la recherche d'un établissement de soin
- Puis-je perdre la vue si j'ai un glaucome? #Il s'agit d'une demande d'expertise médical qui n'est pas dans le cadre de la recherche d'un établissement de soin



Exemples avec contexte conversationnel (TRÈS IMPORTANT):
- Avec historique sur les hôpitaux parisiens, 'Et à Lyon ?' → 1 (question de suivi sur les hôpitaux)
- Avec historique sur les classements, 'Combien coûte une consultation ?' → 0 (question sur les coûts, pas sur les classements)
- Avec historique sur la recherche d'hôpital, 'Merci beaucoup' → 1 (remerciement dans contexte de recherche d'hôpital)
- Avec historique sur hôpitaux publics, 'et privé?' → 1 (question de suivi sur le secteur privé)
- Avec historique sur hôpitaux privés, 'et public?' → 1 (question de suivi sur le secteur public)
- Avec historique sur cardiologie publique, 'privé?' → 1 (question de suivi sur le secteur privé)
- Avec historique mentionnant "privés", 'et privé?' → 1 (demande de précision sur le secteur privé)
- Avec historique sur hôpitaux de Bordeaux, 'publics aussi?' → 1 (question de suivi sur le secteur public)
""",

    "detect_city_prompt": """
Analysez cette phrase pour détecter des informations de localisation.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Une ville peut être mentionnée de manière implicite si le contexte de la conversation montre qu'on parle d'une localisation spécifique.

Répondez avec:
- 0 si aucune localisation n'est mentionnée
- 1 si ville étrangère  
- 2 si confusion entre villes françaises
- 3 si une ville ou localisation française claire est mentionnée

Exemples avec contexte conversationnel:
- Avec historique mentionnant Paris, 'Et à Lyon ?' → 3 (Lyon est mentionné)
- Avec historique sur Marseille, 'Merci' → 0 (aucune nouvelle localisation)
- Avec historique général, 'À Londres ?' → 1 (ville étrangère)
""",

    "second_detect_city_prompt": """
Quelle ville ou département est mentionné par la phrase suivante?

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Une ville peut être mentionnée de manière implicite si le contexte de la conversation montre qu'on parle d'une localisation spécifique.

Si une ville est mentionnée, réponds UNIQUEMENT avec le nom de ville.
Par exemple: pour la phrase 'Trouve moi un hôpital à Lyon', tu me retourneras: 'Lyon'.

Si un département est mentionné, réponds UNIQUEMENT avec le numéro du département.
Par exemple: pour la phrase 'Je veux être hospitalisé dans le 92', tu me retourneras: '92'.               

Si aucune localisation n'est mentionnée dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'.
Par exemple: pour la phrase 'Je veux un classement des meilleurs établissements en France', tu me retourneras: 'aucune correspondance'.
Par exemple: pour la phrase 'Quelle est la meilleur clinique pour une chirurgie à la montagne', tu me retourneras: 'aucune correspondance'.

Exemples avec contexte conversationnel:
- Avec historique mentionnant Paris, 'Et à Lyon ?' → 'Lyon'
- Avec historique sur Marseille, 'Merci' → 'aucune correspondance'
""",

    "detect_number_institutions_prompt": """
Extrayez le nombre d'établissements demandés dans le message suivant.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Le nombre d'établissements peut être mentionné de manière implicite si le contexte de la conversation montre qu'on parle d'un nombre spécifique.

Répondez UNIQUEMENT avec le nombre (1-50) ou 0 si non mentionné.

Par exemple: pour la phrase 'Quels sont les trois meilleurs hôpitaux pour soigner mon audition ?', tu me retourneras: '3'.

Si la phrase inclue une expression comme 'le plus xxx' ou du superlatif qui implique implicitement une seule entité comme 'le meilleur', alors tu me retourneras '1'
Par exemple: pour la phrase 'Quel est la meilleur clinique de Nantes?' ou 'Dis moi l'établissement le plus populaire de France' tu me retourneras: '1'.

Exemples avec contexte conversationnel:
- Avec historique demandant "les 5 meilleurs", 'et privé?' → 5 (garde le nombre du contexte)
- Avec historique général, 'le meilleur' → 1 (nouveau nombre explicite)
- Avec historique sans nombre, 'aussi' → 0 (aucun nombre mentionné)
""",

    "detect_institutions_prompt": """
Ton rôle est d'extraire les noms exacts d'établissements mentionnés dans une question
et de déterminer l'intention de la demande.

---

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

---

INSTRUCTIONS:

1. Extrait tous les noms d'établissements tels qu'ils apparaissent dans le message (même avec fautes ou variantes).
   - Retourne-les tels que l'utilisateur les a écrits, sans corriger ni compléter.
   - Si aucun établissement n'est mentionné, retourne une liste vide.

2. Détermine l'intention de la question :
   - "single" : L'utilisateur parle d'un seul établissement.
   - "multi" : L'utilisateur demande des infos sur plusieurs établissements (mais sans comparaison).
   - "compare" : L'utilisateur compare ou demande un classement.
   - "none" : Pas d'intention claire. S'il y a au moins un établissement qui n'est pas dans la liste, retourne "none".

3. Retourne toujours un objet JSON :
   {
     "institutions": [...],
     "intent": "single|multi|compare|none"
   }

---


EXEMPLES :

1. "Est-ce que l'Hôpital Edouard-Herriot est bon ?"  
{"institutions": ["Hôpital Edouard-Herriot"], "intent": "single"}

2. "Montre-moi les classements pour Hôpital A, Hôpital B et Hôpital C"  
{"institutions": ["Hôpital A", "Hôpital B", "Hôpital C"], "intent": "multi"}

3. "Hôpital Saint-Louis ou Clinique Pasteur, lequel est meilleur ?"  
{"institutions": ["Hôpital Saint-Louis", "Clinique Pasteur"], "intent": "compare"}

4. "Je cherche un hôpital à Toulon"  
{"institutions": [], "intent": "none"}

5. “Est-ce que l’Hôpital Edouard-Herriot est bien pour la cardiologie ?”
{"institutions": ["Hôpital Edouard-Herriot"], "intent": "single"}

6. “Le CHU de Lille est-il recommandé pour la pédiatrie ?”
{"institutions": ["CHU de Lille"], "intent": "single"}

7. “Hôpital Saint-Louis ou Clinique Pasteur, lequel est meilleur pour la neurologie ?”
{"institutions": ["Hôpital Saint-Louis", "Clinique Pasteur"], "intent": "compare"}

8. “CH de Toulon vs CHU de Bordeaux, lequel est le mieux classé ?”
{"institutions": ["CH de Toulon", "CHU de Bordeaux"], "intent": "compare"}

9. “Montre-moi les classements pour CHU de Toulouse, Hôpital Pompidou et CHU de Nantes”
{"institutions": ["CHU de Toulouse", "Hôpital Pompidou", "CHU de Nantes"], "intent": "multi"}

10. “Je cherche un hôpital à Rouen pour la chirurgie cardiaque”
{"institutions": [], "intent": "none"}

11. “Classement CH Roubaix ?”
{"institutions": ["CH Roubaix"], "intent": "single"}

12. “Quels sont les meilleurs hôpitaux pour les urgences en France ?”
{"institutions": [], "intent": "none"}

13. “Le CHU de Grenoble est-il bon en oncologie ?”
{"institutions": ["CHU de Grenoble"], "intent": "single"}

14. “Classement CHU de Lyon et Hôpital Pitié-Salpêtrière pour la neurologie ?”
{"institutions": ["CHU de Lyon", "Hôpital Pitié-Salpêtrière"], "intent": "multi"}

Réponds UNIQUEMENT avec un JSON.

""",

    "detect_institution_type_prompt": """
Détectez le type d'établissement de soin dans le message suivant.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Le type d'établissement peut être mentionné de manière implicite si le contexte de la conversation montre qu'on parle d'un type spécifique.

Répondez UNIQUEMENT avec:
- 0 si aucun type mentionné
- 1 si public
- 2 si privé

Exemples avec contexte conversationnel:
- Avec historique sur les hôpitaux publics, 'et privé?' → 2 (demande maintenant le privé)
- Avec historique sur les hôpitaux privés, 'et public?' → 1 (demande maintenant le public)
- Avec historique général, 'aussi' → 0 (aucun type spécifique mentionné)
""",

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

Reformulez en une question complète et précise qui combine tous les critères:
"""
}
