"""
Prompt instructions for detection tasks.
"""

from typing import Dict

DETECTION_PROMPT_INSTRUCTIONS: Dict[str, str] = {
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
Voici un message pour lequel tu vas devoir détecter la ou les pathologie(s) ou spécialité(s) médicale(s) mentionnées ou sous-entendues.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Si un historique de conversation est fourni ci-dessus, analyse le nouveau message en tenant compte du contexte conversationnel. Une spécialité ou pathologie peut être mentionnée de manière implicite si le contexte montre qu'on parle d'un sujet médical spécifique.

Ta tâche :
- Liste toutes les pathologies ou spécialités médicales que tu détectes dans le message (même si elles sont implicites ou sous-entendues).
- Si tu détectes plusieurs spécialités/pathologies, liste-les séparées par une virgule.
- Si aucune spécialité/pathologie médicale n'est détectée, réponds exactement : 'aucune correspondance'.
- N'invente pas de spécialité ou pathologie qui n'est pas mentionnée ou sous-entendue dans le message.

Exemples :
- Pour le message 'Je veux soigner mon AVC?', tu répondras 'Accidents vasculaires cérébraux'.
- Pour le message 'Je cherche un hôpital pour un accouchement', tu répondras 'Accouchements à risques, Accouchements normaux' (si les deux sont sous-entendus).
- Pour le message 'J'ai mal au genou', tu répondras 'genou' (si les deux sont sous-entendus).
- Pour le message 'Quel est le classement de CH de Vannes pour la cancer au sein ?', tu répondras 'Cancer du sein'.
- Pour le message 'Quels sont les meilleurs hôpitaux pour la cataracte ?', tu répondras 'Cataracte'.
- Pour le message 'Quels sont les meilleurs hôpitaux à Paris ?', tu répondras 'aucune correspondance'.

N'invente pas de spécialité qui n'est pas dans le message ou le contexte.
""",
"detect_location_prompt": """
Analysez ce message pour déterminer s’il contient une ou plusieurs localisations.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Règles:
- Une localisation peut être : une ville/commune française, un département (numéro ou nom) français, une région française, un code postal (ex: "75015", "13001")
- Si la localisation est uniquement mentionnée dans un nom d’institution (par ex. "Hôpital Paris Saint-Joseph", "Université de Strasbourg", "Clinique de Lille"), ignorez-la.
- Si un historique de conversation est fourni ci-dessus, analysez le nouveau message en tenant compte du contexte conversationnel. Une ville peut être mentionnée de manière implicite si le contexte de la conversation montre qu'on parle d'une localisation spécifique.
- Répondez UNIQUEMENT avec un code numérique :
  - 0 → aucune localisation
  - 1 → ville étrangère
  - 2 → confusion entre villes françaises
  - 3 → une localisation française claire (ville, département, région, ou code postal)

Exemples:
- "Je veux un hôpital en France" → 0
- "Trouve-moi un hôpital à Lyon" → 3
- "Je veux être hospitalisé dans le 92" → 3
- "Je veux être hospitalisé dans le Val d'Oise" → 3
- "Quels sont les établissements en Île-de-France ?" → 3
- "Clinique du Val de Loire" → 0 (institution → ignoré)
- "Je veux le meilleur clinique à New York" → 1
- "Je parle de Paris, ou de Lyon ?" → 2
- "Donnes-moi les 3 meilleurs hopitaux dans le 75015" → 3
- Avec historique sur Paris : "Et à Lyon ?" → 3
- Avec historique sur Marseille : "Merci" → 0

""",

    "second_detect_location_prompt": """
Analysez le message suivant pour extraire toutes les localisations présentes.

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

Règles:
1. Une localisation peut être :
   - Ville/commune → retournez {{"type": "city_commune", "value": "<nom de la ville>"}} ou {{"type": "city_commune", "value": ["ville1", "ville2", ...]}} si plusieurs villes sont détectées
   - Département (nom uniquement) → retournez {{"type": "department", "value": "<nom du département>"}} ou {{"type": "department", "value": ["dept1", "dept2", ...]}}
   - Département numéro (numéro uniquement) → retournez {{"type": "department_number", "value": "<numéro>"}} ou {{"type": "department_number", "value": ["num1", "num2", ...]}}
   - Région → retournez {{"type": "region", "value": "<nom de la région>"}} ou {{"type": "region", "value": ["region1", "region2", ...]}}
   - Code postal → retournez {{"type": "postal_code", "value": "<code postal>"}} ou {{"type": "postal_code", "value": ["code1", "code2", ...]}}
2. Si aucune localisation n’est mentionnée → retournez {{"type": "none", "value": "aucune correspondance"}}
3. Si une localisation apparaît uniquement dans un nom d’institution (par ex. "Hôpital Paris Saint-Joseph", "Université de Strasbourg", "Clinique de Lille"), ignorez-la et retournez {{"type": "none", "value": "aucune correspondance"}}
4. Utilisez le contexte conversationnel si disponible.
5. Chaque type ne doit apparaître **qu’une seule fois**, et sa valeur doit contenir tous les éléments détectés (liste si nécessaire).

Exemples avec localisation:
- "Trouve moi un hôpital à Lyon" → {{"type": "city", "value": "Lyon"}}
- "Je veux être hospitalisé dans le 92" → {{"type": "department_number", "value": "92"}}
- "Je veux être hospitalisé dans le Val d'Oise" → {{"type": "department", "value": "Val d'Oise"}}
- "Quels sont les établissements en Île-de-France" → {{"type": "region", "value": "Île-de-France"}}
- "Donnes-moi les 3 meilleurs hopitaux dans le 75015" → {{"type": "postal_code", "value": "75015"}}
- "Trouve-moi un hôpital à Lyon (75015)" → [{{"type": "city_commune", "value": "Lyon"}}, {{"type":"postal_code","value":"75015"}}]
- "Hôpitaux à Lyon et dans le 92" → [{{"type": "city_commune", "value": ["Lyon"]}}, {{"type": "department_number", "value": ["92"]}}]
- "Établissements à Lyon, Marseille et 75015" → [{{"type": "city_commune", "value": ["Lyon", "Marseille"]}}, {{"type": "postal_code", "value": ["75015"]}}]

Exemples sans localisation:
- "Donnes-moi le classement de Clinique du Val de Loire" → {{"type": "none", "value": "aucune correspondance"}}
- "C'est bien le clinique de l'université de Paris ?" → {{"type": "none", "value": "aucune correspondance"}}
- "Je veux un classement des meilleurs établissements en France" → {{"type": "none", "value": "aucune correspondance"}}
- "Quelle est la meilleur clinique pour une chirurgie à la montagne ?" → {{"type": "none", "value": "aucune correspondance"}}

Exemples avec contexte conversationnel:
- Avec historique sur Paris : "Et à Lyon ?" → {{"type": "city", "value": "Lyon"}}
- Avec historique sur Marseille : "Merci" → {{"type": "none", "value": "aucune correspondance"}}
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
Ton rôle est d'extraire les noms exacts d'établissements mentionnés dans une question et de déterminer l'intention de la demande.

---

HISTORIQUE DE CONVERSATION:
{conv_history}

MESSAGE À ANALYSER: '{prompt}'

---

INSTRUCTIONS:

1. Extrait tous les noms d'établissements tels qu'ils apparaissent dans le message (même avec fautes ou variantes).
   - Retourne-les tels que l'utilisateur les a écrits, sans corriger ni compléter.
   - Si aucun établissement n'est mentionné, retourne une liste vide.
   - NE RETOURNE PAS de mots génériques ou de catégories comme "hôpital", "hôpitaux", "clinique", "cliniques", "établissement", "établissements", "centre", "centres", "hôpital public", "hôpital privé", "hôpitaux publics", "hôpitaux privés", "cliniques privées", "cliniques publiques", ni de noms de villes ou régions.
   - NE RETOURNE PAS de sigles ou abréviations génériques comme "CH", "CHU", "CHR", "CHRU" s'ils sont seuls, sans nom de ville ou de site associé (ex: "CH de Vannes" est correct, mais "CH" seul ne l'est pas).
   - Ne considère comme établissement que les noms propres ou dénominations précises d'un hôpital ou d'une clinique (ex: "CH de Vannes", "Hôpital Edouard-Herriot", "Clinique Pasteur").

2. Détermine l'intention de la question :
   - "single" : L'utilisateur parle d'un seul établissement (même si le mot "classement" est utilisé, s'il n'y a qu'un seul nom d'établissement, l'intention est "single").
   - "multi" : L'utilisateur demande des infos sur plusieurs établissements (mais sans comparaison).
   - "compare" : L'utilisateur compare ou demande un classement entre plusieurs établissements (utilise des formulations comme "lequel est meilleur", "vs", "comparaison", etc. ET il y a au moins deux établissements mentionnés).
   - "none" : Pas d'intention claire. S'il y a au moins un établissement qui n'est pas dans la liste, retourne "none".

3. Retourne toujours un objet JSON :
   {{
     "institutions": [...],
     "intent": "single|multi|compare|none"
   }}

---

EXEMPLES :

1. "Est-ce que l'Hôpital Edouard-Herriot est bon ?"  
{{"institutions": ["Hôpital Edouard-Herriot"], "intent": "single"}}

2. "Montre-moi les classements pour Hôpital A, Hôpital B et Hôpital C"  
{{"institutions": ["Hôpital A", "Hôpital B", "Hôpital C"], "intent": "multi"}}

3. "Hôpital Saint-Louis ou Clinique Pasteur, lequel est meilleur ?"  
{{"institutions": ["Hôpital Saint-Louis", "Clinique Pasteur"], "intent": "compare"}}

4. "Je cherche un hôpital à Toulon"  
{{"institutions": [], "intent": "none"}}

5. “Est-ce que l’Hôpital Edouard-Herriot est bien pour la cardiologie ?”
{{"institutions": ["Hôpital Edouard-Herriot"], "intent": "single"}}

6. “Le CHU de Lille est-il recommandé pour la pédiatrie ?”
{{"institutions": ["CHU de Lille"], "intent": "single"}}

7. “Hôpital Saint-Louis ou Clinique Pasteur, lequel est meilleur pour la neurologie ?”
{{"institutions": ["Hôpital Saint-Louis", "Clinique Pasteur"], "intent": "compare"}}

8. “CH de Toulon vs CHU de Bordeaux, lequel est le mieux classé ?”
{{"institutions": ["CH de Toulon", "CHU de Bordeaux"], "intent": "compare"}}

9. “Montre-moi les classements pour CHU de Toulouse, Hôpital Pompidou et CHU de Nantes”
{{"institutions": ["CHU de Toulouse", "Hôpital Pompidou", "CHU de Nantes"], "intent": "multi"}}

10. “Je cherche un hôpital à Rouen pour la chirurgie cardiaque”
{{"institutions": [], "intent": "none"}}

11. “Classement CH Roubaix ?”
{{"institutions": ["CH Roubaix"], "intent": "single"}}

12. “Quels sont les meilleurs hôpitaux pour les urgences en France ?”
{{"institutions": [], "intent": "none"}}

13. “Le CHU de Grenoble est-il bon en oncologie ?”
{{"institutions": ["CHU de Grenoble"], "intent": "single"}}

14. “Classement CHU de Lyon et Hôpital Pitié-Salpêtrière pour la neurologie ?”
{{"institutions": ["CHU de Lyon", "Hôpital Pitié-Salpêtrière"], "intent": "multi"}}

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
"""
}