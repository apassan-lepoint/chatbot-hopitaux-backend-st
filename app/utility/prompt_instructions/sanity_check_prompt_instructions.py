"""
Sanity check prompt instructions for medical pertinence and chatbot pertinence.
"""

from typing import Dict

SANITY_CHECK_PROMPT_INSTRUCTIONS: Dict[str, str] = {
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
}

