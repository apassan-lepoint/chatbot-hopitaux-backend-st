import os
from langchain_community.chat_models import ChatOpenAI
import pandas as pd
from dotenv import load_dotenv

from app.utils.prompts import prompt_instructions
from app.utils.specialties import specialties_dict
from app.utils.formatting import format_mapping_words_csv, format_correspondance_list


class Appels_LLM:
    def __init__(self):
        load_dotenv()
        self.model = self.init_model()
        self.palmares_df = None
        self.etablissement_name=None
        self.specialty= None#Variable qui contient le nom de la spécialité dans la question de l'utilisateur
        self.ispublic= None#Variable qui contient le type d'établissement public/privé de la question de l'utilisateur
        self.city = None#Variable qui contient la ville de la question de l'utilisateur
        self.établissement_mentionné = None
        self.paths={
                "mapping_word_path":r"data\resultats_llm_v5.csv",
                "palmares_path":r"data\classments-hopitaux-cliniques-2024.xlsx",
                "coordonnees_path":r"data\fichier_hopitaux_avec_coordonnees_avec_privacitée.xlsx"
            }
        
        self.key_words=self.format_mapping_words_csv(self.paths["mapping_word_path"])

    def init_model(self) -> ChatOpenAI:
        api_key = os.getenv("API_KEY")

        # Initialise le modèle 
        self.model = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4o-mini"
        )
        return self.model
    
    def get_specialty_list(self):
        #On récupère la liste des spécialités depuis le fichier excel qui liste les palmarès
        df_specialty = pd.read_excel(self.paths["palmares_path"] , sheet_name="Palmarès")
        self.palmares_df=df_specialty
        colonne_1 = df_specialty.iloc[:, 0].drop_duplicates()
        liste_spe = ", ".join(map(str, colonne_1.dropna()))
        return liste_spe
        
    def get_speciality(self, 
    prompt: str #Question de l'utilisateur
    ) -> str:
        # Détermine la spécialité médicale correspondant à la question.

        liste_spe=self.get_specialty_list()
        #On fait appel au LLM pour déterminer la spécialité concernée
        get_speciality_prompt_formatted=prompt_instructions["get_speciality_prompt"].format(liste_spe=liste_spe,prompt=prompt)
        self.specialty = self.model.predict(get_speciality_prompt_formatted).strip()

        specialties = specialties_dict
        
        if ',' in self.specialty and not self.specialty.startswith('plusieurs correspondances:'):
            self.specialty = 'plusieurs correspondances: ' + self.specialty
            
        

        if self.specialty.startswith("plusieurs correspondances:"):
            def get_specialty_keywords(message, specialties):
                for category, keywords in specialties.items():
                    if any(keyword.lower() in message.lower() for keyword in keywords):
                        return "plusieurs correspondances:"+f"{','.join(keywords)}"
            liste_spe= get_specialty_keywords(self.specialty, specialties)
            self.specialty=self.format_correspondance_list(liste_spe)
            return self.specialty
        else:
            if self.specialty == 'aucune correspondance':
                # Si on a aucune correspondance dans un premier temps, on va rappeler le llm en lui fournissant une liste de mots clés qui lui permettrait d'effectuer un matching
                mapping_words=self.key_words
                second_get_speciality_prompt_formatted=prompt_instructions["second_get_speciality_prompt"].format(prompt=prompt,mapping_words=mapping_words)
                self.specialty = self.model.predict(second_get_speciality_prompt_formatted).strip()
                return self.specialty
        return self.specialty

    def get_offtopic_approfondi(self, 
    prompt: str #Question de l'utilisateur
    ) -> str:
        # Détermine si la question est pertinente dans le cadre d'un assistant au palmarès des hôpitaux
        formatted_prompt=prompt_instructions["get_offtopic_approfondi_prompt"].format(prompt=prompt)
        res = self.model.predict(formatted_prompt).strip()
        return res
    
    def get_offtopic(self, 
    prompt: str #Question de l'utilisateur
    ) -> str:
        # Détermine si la question est hors sujet
        formatted_prompt=prompt_instructions["get_offtopic_prompt"].format(prompt=prompt)
        self.isofftopic = self.model.predict(formatted_prompt).strip()
        return self.isofftopic

    def get_city(self, 
    prompt: str #Question de l'utilisateur
    ) -> str:
        # Identifie la ville ou le département mentionné dans une phrase.

        #On va d'abord détecter via un appel llm si la ville peut comprter une ambiguité: homonymes en France, nom incomplet etc
        formatted_prompt = prompt_instructions["get_city_prompt"].format(prompt=prompt)
        self.city = self.model.predict(formatted_prompt).strip()

        #S'il n'y a pas d'ambiguité on va récupérer le nom de la ville dans un deuxième temps via un appel LLM
        if self.city=='correct':
            formatted_prompt = prompt_instructions["get_city_prompt_2"].format(prompt=prompt)
            self.city = self.model.predict(formatted_prompt).strip()
        return self.city

    def get_topk(self, 
    prompt: str #Question de l'utilisateur
    ):
        # Identifie si le nombre d'établissements à afficher est mentionné dans la phrase de l'utilisateur.

        formatted_prompt = prompt_instructions["get_topk_prompt"].format(prompt=prompt)
        topk = self.model.predict(formatted_prompt).strip()
        if topk!='non mentionné':
            #On limite à 50 la liste d'établissmeents à afficher
            if int(topk)>50:
                topk='non mentionné'
            else:
                topk=int(topk)
        return topk

    def get_etablissement_list(self):
        #Permet d'obtenir une liste formatée avec les établissements présent dans les classements
        coordonnees_df = pd.read_excel(self.paths["coordonnees_path"])#Ce df contient la liste des établissments
        colonne_1 = coordonnees_df.iloc[:, 0]
        liste_etablissement = [element.split(",")[0] for element in colonne_1]#On enlève toutes les localisations situées après les virgules qui pourraient fausser notre recherche de matchs
        liste_etablissement = list(set(liste_etablissement))
        liste_etablissement = [element for element in liste_etablissement if element != "CHU"]
        liste_etablissement = [element for element in liste_etablissement if element != "CH"]
        liste_etablissement = ", ".join(map(str, liste_etablissement))
        return liste_etablissement

    def is_public_or_private(self, 
    prompt: str #Question de l'utilisateur
    ) -> str:
        # Détermine si la question mentionne un hôpital publique,privé ou pas. Détermine aussi si un hôpital en particulier est mentionné

        #On va dans un premier temps lister les établissements des classements 
        liste_etablissement=self.get_etablissement_list()

        #On va ensuite appeler notre LLM qui va pouvoir détecter si l'un des établissements est mentionné dans la question de l'utilisateur
        formatted_prompt =prompt_instructions["is_public_or_private_prompt"].format(liste_etablissement=liste_etablissement,prompt=prompt) 
        self.etablissement_name = self.model.predict(formatted_prompt).strip()

  
        if self.etablissement_name in liste_etablissement:
            self.établissement_mentionné = True
            if self.établissement_mentionné:
                self.city='aucune correspondance'
            #On récupère la catégorie de cet établissment
            coordonnees_df = pd.read_excel(self.paths["coordonnees_path"])
            ligne_saut = coordonnees_df[coordonnees_df['Etablissement'].str.contains(self.etablissement_name,case=False, na=False)]
            self.ispublic = ligne_saut.iloc[0,4]
        else:
            #Si aucun établissement n'est détecté on va rechercher si un critère public/privé est mentionné
            formatted_prompt = prompt_instructions["is_public_or_private_prompt2"].format(prompt=prompt) 
            ispublic = self.model.predict(formatted_prompt).strip()
            self.établissement_mentionné = False
            self.ispublic = ispublic
        return self.ispublic

    def continuer_conv(self, 
    prompt: str ,#Question de l'utilisateur
    conv_history: list #historique de la conversation avec l'utilisateur
    ) -> str:
        # Réponds à la nouvelle question de l'utilisateur
        formatted_prompt = prompt_instructions["continuer_conv_prompt"].format(prompt=prompt,conv_history=conv_history) 
        self.newanswer  = self.model.predict(formatted_prompt).strip()
        return self.newanswer