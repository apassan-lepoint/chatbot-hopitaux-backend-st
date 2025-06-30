"""
This module contains prompt templates for interacting with the LLM.

Each prompt is designed for a specific task: identifying medical specialties,
    detecting off-topic questions, extracting city names, or continuing conversations.

The prompts use placeholders (e.g., {prompt}, {specialty_list}) to be filled dynamically
at runtime.

Attributes:
    prompt_instructions (dict): 
        Keys (str): Names of the prompts.
        Values (str): Template strings for each prompt.
"""

prompt_instructions = {
    "detect_speciality_prompt":
        """
        Voici un message pour lequel tu vas devoir choisir la spécialité qui correspond le plus. Voici mon message  :{prompt}.
        Voici une liste de spécialité pour laquelle tu vas devoir choisir la spécialité qui correspond le plus à mon message  : liste des spécialités: '{specialty_list}'? 

        Consignes:
        Si une seule spécialité de la liste correspond à ma demande, réponds UNIQUEMENT avec la spécialité exacte de la liste. 
        Exemple:  Pour le message 'Quel est le meilleur hôpital d'audition?', tu me répondras 'Audition'.
        Exemple:  Pour le message 'Je veux soigner mon AVC?', tu me répondras 'Accidents vasculaires cérébraux'.

        Si plusieurs spécialités de la liste peuvent correspondre ou sont liées à le message, réponds UNIQUEMENT avec les spécialités exactes de la liste et sous le format suivant: 'plusieurs correspondances: spécialité 1, spécialité 2'.
        Exemple: pour le message 'Je cherche un hôpital pour un accouchement', tu me répondras 'plusieurs correspondances: Accouchements à risques, Accouchements normaux'.
        Exemple: pour le message 'J'ai mal au genou', tu me répondras 'plusieurs correspondances: Prothèse de genou, Ligaments du genou'.

        Si aucune Spécialité de la liste est liée à ma demande, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'
        N'invente pas de spécialité qui n'est pas dans la liste
        """
        ,

    "second_detect_speciality_prompt":
        """
        Voici un message pour lequel tu vas devoir trouver la ou les pathologie(s) qui correspondent le plus: '{prompt}'
        Voici la liste des pathologies et des mots clés associés pour t'aider:{mapping_words}
        
        Si une seule spécialité de la liste correspond à ma demande, réponds UNIQUEMENT avec la spécialité exacte de la liste. 
        Exemple:  Pour le message 'Je veux soigner mon AVC?', tu me répondras 'Accidents vasculaires cérébraux'.

        Si plusieurs spécialités de la liste peuvent correspondre ou sont liées à le message, réponds UNIQUEMENT avec les spécialités exactes de la liste et sous le format suivant: 'plusieurs correspondances: spécialité 1, spécialité 2'.
        Exemple: pour le message 'Je cherche un hôpital pour un accouchement', tu me répondras 'plusieurs correspondances: Accouchements à risques, Accouchements normaux'.
        Exemple: pour le message 'J'ai mal au genou', tu me répondras 'plusieurs correspondances: Prothèse de genou, Ligaments du genou'.

        Si aucune Spécialité de la liste est liée à ma demande, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'
        N'invente pas de spécialité qui n'est pas dans la liste
        """
        ,


    "check_medical_pertinence_prompt":
        """
        Évaluez si le message suivant a un rapport avec la santé humaine ou les services de soins. 
        Si le message a un rapport avec le médical, retourne EXACTEMENT ce mot: 'Pertinent'.
        Par exemple pour le message: 'J'ai un cancer à Paris' , tu retourneras: 'Pertinent'.
        Par exemple pour le message: 'Cataracte' , tu retourneras: 'Pertinent'.
        Par exemple pour le message: 'J'ai mal aux pieds' , tu retourneras: 'Pertinent'.
        Par exemple pour le message: 'Les hôpitaux privés sont ils meilleurs que les publiques?' , tu retourneras: 'Pertinent'.

        Si le message est hors sujet et n'a aucun rapport avec le domaine médical, retourne EXACTEMENT ces deux mots: 'Hors sujet'. 
        Par exemple pour le message: 'Je mange des frites' , tu retourneras: 'Hors sujet'.
        Voici le Message : '{prompt}'
        """
        ,


    "check_chatbot_pertinence_prompt":
        """
        Tu es un chatbot assistant chargé de vérifier si une question d'un utilisateur est pertinente pour un classement annuel des hôpitaux.  
        Voici la question de l'utilisateur:'{prompt}'

        Une question est dite "pertinente" si elle concerne au moins un des cas suivants:
        - Une maladie, un symptôme ou une spécialité médicale  
        - Le classement des hôpitaux et cliniques  
        - La recherche d’un hôpital, d’une clinique ou d’un service médical  
        

        Si la question est pertinente, réponds uniquement par "pertinent".  
        Sinon, réponds uniquement par "hors sujet".  

        Exemples de questions pertinentes :  
        - Quel est la meilleur clinique de France ?
        - Conseille moi un hôpital à Lyon 
        - Je chercher un service de pneumologie
        - Où faire soigner mon glaucome ? 
        - Je veux corriger mon audition
        - Il y a fréquemment du sang dans mes urines. Conseille-moi un hôpital. 
        - Je veux cherche à faire soigner mes troubles bipôlaires
        - Est-ce que l'Institut mutualiste Montsouris est bon ?
        -Y a-t-il des hôpitaux privés avec un service de cardiologie interventionnelle ?

        Exemples de questions non pertinentes :  
        - Pourquoi les hôpitaux sont-ils en crise ?  #Il s'agit d'une demande d'information qui n'est pas dans le cadre direct de la recherche d'un établissement de soin
        - Dois-je prendre du paracétamol pour ma fièvre ? #Il s'agit d'une demande d'expertise médical qui n'est pas dans le cadre de la recherche d'un établissement de soin
        - Puis-je perdre la vue si j'ai un glaucome? #Il s'agit d'une demande d'expertise médical qui n'est pas dans le cadre de la recherche d'un établissement de soin

        """
        ,

    "detect_city_prompt":
        
        """ 
        Je vais te donner une phrase pour laquelle tu vas devoir déterminer si elle comporte un nom de ville qui peut porter à confusion. Voici la phrase '{prompt}'?
        Si une ville mentionnée dans la phrase peut porter confusion entre plusieurs villes françaises alors tu vas me renvoyer: 'confusion'.
        Si plusieurs villes en France portent ce nom, alors tu vas me renvoyer: 'confusion'.
        Par exemple:  pour la phrase, 'Soigne moi à Saint-Paul', tu me retourneras: 'confusion'.
        Par exemple:  pour la phrase, 'Quelle est la meilleure clinique privée de Montigny?', tu me retourneras: 'confusion'.
        Par exemple:  pour la phrase, 'Je suis à Valmont?', tu me retourneras: 'confusion'.                 

        Si aucune localisation n'est précisée , renvoie moi EXACTEMENT ce mot: 'correct'.
        Par exemple:  pour la phrase, 'Je veux soigner mon audition', tu me retourneras: 'correct'.
        
        Si une localisation est précisée et ne porte pas à confusion, renvoie moi EXACTEMENT ce mot: 'correct'.    
        Par exemple:  pour la phrase, 'Je veux un classement des meilleurs établissements de Reims', tu me retourneras: 'correct'.
        Par exemple:  pour la phrase, 'Quelle est la meilleur clinique Lyonnaise', tu me retourneras: 'correct'.
        
        Si la ville mentionnée n'est pas située en France, renvoie moi EXACTEMENT ces deux mots: 'ville étrangère'.
        Par exemple:  pour la phrase, 'Soigne moi dans une ville mexicaine', tu me retourneras: 'ville étrangère'. 
        """
        ,

    "second_detect_city_prompt":
            """ 
            Quelle ville ou département est mentionné par la phrase suivante : '{prompt}'?
            Si une ville est mentionnée, réponds UNIQUEMENT avec le nom de ville.
            Par exemple:  pour la phrase, 'Trouve moi un hôpital à Lyon', tu me retourneras: 'Lyon'.

            Si un département est mentionné, réponds UNIQUEMENT avec le numéro du département.
            Par exemple:  pour la phrase, 'Je veux être hospitalisé dans le 92', tu me retourneras: '92'.               

            Si aucune localisation n'est mentionnée dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'.
            Par exemple:  pour la phrase, 'Je veux un classement des meilleurs établissements en France', tu me retourneras: 'aucune correspondance'.
            Par exemple:  pour la phrase, 'Quelle est la meilleur clinique pour une chirurgie à la montagne', tu me retourneras: 'aucune correspondance'.
            """
        ,

        "detect_topk_prompt":
            """ 
            Un numéro de classement est il mentionné dans la phrase suivante : '{prompt}'?
            Si un numéro de classement est mentionnée, réponds UNIQUEMENT avec le nombre associé.
            Par exemple: pour la phrase 'Quels sont les trois meilleurs hôpitaux pour soigner mon audition ?', tu me retourneras: '3'.

            Si aucune numéro de classement n'est mentionnée dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'non mentionné'.
            Par exemple:  pour la phrase, 'je veux un classement des meilleurs établissement en France', tu me retourneras: 'non mentionné'.

            Si la phrase inclue une expression comme 'le plus xxx' ou du superlatif qui implique implicitement une seule entité comme 'le meilleur', alors tu me retourneras '1'
            Par exemple: pour la phrase 'Quel est la meilleur clinique de Nantes?' ou 'Dis moi l'établissement le plus populaire de France' tu me retourneras: '1'.
            
            """
        ,

        "detect_institution_type_prompt":
            """
            Un des noms exact de ma liste d'établissements est il mentionné précisément dans cette phrase: '{prompt}'? Voici ma liste d'établissements:
            {institution_list}
            Réponds UNIQUEMENT avec le nom d'établissement exact de la liste si la phrase contient un des noms exacts d'établissement.
            Si aucun de ces établissement n'est mentionné dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'.
            Si la Ville de l'établissement est mentionnée mais pas le nom complet, par exemple 'Villeneuve-d’Ascq' est mentionné mais pas 'Clinique de Villeneuve-d’Ascq' alors tu renverras 'aucune correspondance'. 
            
            
            Voici des exemples sans noms d'établissement: pour la phrase 'Je cherche un hôpital pour soigner mon audition à Toulon ?' ou 'Quelle est la meilleure clinique de Limoges?', tu me répondras 'aucune correspondance'.
            Voici un exemple avec noms d'établissement: pour la phrase 'Est-ce que l'Hôpital Edouard-Herriot est bon en cas de problèmes auditifs ?' tu me répondras 'Hôpital Edouard-Herriot'. 
            """
        ,

        "second_detect_institution_type_prompt":
            """ 
            Le type d'établissement de soin publique ou privé/clinique est il mentionné dans cette phrase : '{prompt}'?
            Si aucun type d'établissement n'est mentionné dans ma phrase, renvoie moi EXACTEMENT ces deux mots: 'aucune correspondance'.
            Si un type d'établissement est mentionné réponds UNIQUEMENT avec le mot 'Public' pour un établissement publique mentionné ou 'Privé' pour une clinique ou un établissement privé.
            """
        ,

        "continue_conversation_prompt":
        """
        Vous êtes un assistant intelligent. Voici l'historique de la conversation précédente entre l'utilisateur et vous :{conv_history}
        Réponds au nouveau message de l'utilisateur:{prompt}
        """

        ,
        
        "detect_modification_prompt": """
        Vous êtes un assistant pour un chatbot médical qui convertit des questions en requêtes SQL.

        Voici l'historique de la conversation : {conv_history}
        Voici le nouveau message de l'utilisateur : {prompt}

        Votre tâche est de déterminer si ce nouveau message :
        - modifie ou précise la question précédente,
        - ou constitue une nouvelle question indépendante.

        Répondez uniquement avec l’un des trois mots suivants (en minuscules, sans ponctuation) :
        - modification
        - nouvelle question
        - ambiguous

        Si le message semble à la fois potentiellement lié et potentiellement indépendant, répondez 'ambiguous'.

        Voici quelques exemples pour vous guider :

        ### Cas : modification
        Le nouveau message complète, reformule ou précise la question précédente.

        1.  
            Historique : "Quels sont les hôpitaux à Bordeaux ?"  
            Nouveau message : "Seulement les hôpitaux publics, s'il te plaît."  
            → Réponse attendue : **modification**

        2.  
            Historique : "Montre-moi les cliniques privées à Lyon."  
            Nouveau message : "Ajoute une condition sur la spécialité : dermatologie."  
            → Réponse attendue : **modification**

        3.  
            Historique : "Quels établissements ont un taux de satisfaction supérieur à 90 % ?"  
            Nouveau message : "Maintenent juste à Paris"  
            → Réponse attendue : **modification**
        4. 
            Historique : "Top 5 des hôpitaux publics spécialisés en oncologie."  
            Nouveau message : "Et pour la gynécologie à Nantes ?"  
            → Réponse attendue : **modification** (même nombre des institutions; mais spécialité et ville différentes)
            
        5. 
            Historique : "Montre-moi les hôpitaux publics."  
            Nouveau message : "Et ceux qui ont un bon service d’oncologie ?"  
            → Réponse attendue : **modification** (même type d'institution; mais spécialité différente)

        ### Cas : nouvelle question
        Le nouveau message pose une question complètement indépendante.

        1.  
             Historique : "Quels sont les hôpitaux publics en Provence-Alpes-Côte d'Azur ?"  
            Nouveau message : "Top 10 des établissements privés à Lille en dermatologie."  
            → Réponse attendue : **nouvelle question**

        2.  
            Historique : "Donne-moi les meilleurs hôpitaux pour la cardiologie à Bordeaux."  
            Nouveau message : "Quels sont les établissements privés en Normandie ?"  
            → Réponse attendue : **nouvelle question**
        
        3. 
            Historique : "Quels sont les centres spécialisés en neurologie ?"  
            Nouveau message : "Et pour la psychiatrie ?"  
            → Réponse attendue : **nouvelle question ** (il n'y avait qu'une seule spécification pour une requête dans le message d'origine, qui a été modifiée dans le message suivant)

        ### Cas : ambiguous
        Le lien avec la question précédente est possible mais pas évident sans plus de contexte.

        1.  
            Historique : "Quels sont les établissements de santé à Toulouse ?"  
            Nouveau message : "Et ceux qui sont bien notés ?"  
            → Réponse attendue : **ambiguous**
        """
        
        ,
        
        "rewrite_query_prompt": """
        Voici la question initiale de l'utilisateur :
        {last_query}

        Voici la modification ou précision apportée par l'utilisateur :
        {modification}

        Reformule une nouvelle question complète et précise qui prend en compte la modification.
        """
}