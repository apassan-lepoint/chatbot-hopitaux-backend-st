"""
Service for interacting with the language model (LLM).

This file defines the Appels_LLM class, which handles all LLM-based extraction of
    specialties, cities, institution types, and other information from user queries.
"""

import os
from langchain_community.chat_models import ChatOpenAI
import pandas as pd
from dotenv import load_dotenv

from app.utils.prompts import prompt_instructions
from app.utils.specialties import specialties_dict
from app.utils.formatting import format_mapping_words_csv, format_correspondance_list


class Appels_LLM:
    """
    Handles all interactions with the language model (LLM) for extracting relevant information
        from user queries/prompts. 
    """
    
    def __init__(self):
        """
        Initializes the Appels_LLM class by loading environment variables, setting up the LLM model with different 
            parameters for the query, and preparing file paths and keyword mappings.
        """
        
        load_dotenv(override = False) 
        self.model = self.init_model()
        self.palmares_df = None
        self.etablissement_name=None
        self.specialty= None
        self.ispublic= None
        self.city = None
        self.établissement_mentionné = None
        
        self.paths={
                "mapping_word_path":r"data\resultats_llm_v5.csv",
                "palmares_path":r"data\classments-hopitaux-cliniques-2024.xlsx",
                "coordonnees_path":r"data\fichier_hopitaux_avec_coordonnees_avec_privacitée.xlsx"
            }
        
        self.key_words=self.format_mapping_words_csv(self.paths["mapping_word_path"])

    def init_model(self) -> ChatOpenAI:
        """
        Initializes and returns the ChatOpenAI model using the API key from environment variables.

        Returns:
            ChatOpenAI: An instance of the ChatOpenAI model.
        """
        
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4o-mini"
        )
        return self.model
    
    def get_specialty_list(self):
        """
        Retrieves the list of medical specialties from the rankings Excel file.

        Returns:
            str: A comma-separated string of all specialties.
        """
        df_specialty = pd.read_excel(self.paths["palmares_path"] , sheet_name="Palmarès")
        self.palmares_df=df_specialty
        colonne_1 = df_specialty.iloc[:, 0].drop_duplicates()
        liste_spe = ", ".join(map(str, colonne_1.dropna()))
        return liste_spe
        
    def get_speciality(self, prompt: str) -> str:
        """
        Determines the medical specialty relevant to the user's question using the LLM.
        
        If no clear match is found, it attempts a second detection using keyword mapping.

        Args:
            prompt (str): The user's question.

        Returns:
            str: The detected specialty or a message indicating no match.
        """

        liste_spe=self.get_specialty_list()
        #On fait appel au LLM pour déterminer la spécialité concernée
        get_speciality_prompt_formatted=prompt_instructions["get_speciality_prompt"].format(liste_spe=liste_spe,prompt=prompt)
        self.specialty = self.model.predict(get_speciality_prompt_formatted).strip()

        specialties = specialties_dict
        
        # If multiple matches are detected, format accordingly
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
                # Retry with keyword mapping if no match is found
                mapping_words=self.key_words
                second_get_speciality_prompt_formatted=prompt_instructions["second_get_speciality_prompt"].format(prompt=prompt,mapping_words=mapping_words)
                self.specialty = self.model.predict(second_get_speciality_prompt_formatted).strip()
                return self.specialty
        return self.specialty

    def get_offtopic_approfondi(self, prompt: str) -> str:
        """
        Determines if the user's question is relevant to the hospital ranking assistant.

        Args:
            prompt (str): The user's question.

        Returns:
            str: The LLM's assessment of relevance.
        """
        
        formatted_prompt=prompt_instructions["get_offtopic_approfondi_prompt"].format(prompt=prompt)
        res = self.model.predict(formatted_prompt).strip()
        return res
    
    def get_offtopic(self, prompt: str) -> str:
        """
        Determines if the user's question is off-topic for the assistant.

        Args:
            prompt (str): The user's question.

        Returns:
            str: The LLM's off-topic assessment.
        """

        formatted_prompt=prompt_instructions["get_offtopic_prompt"].format(prompt=prompt)
        self.isofftopic = self.model.predict(formatted_prompt).strip()
        return self.isofftopic

    def get_city(self, prompt: str) -> str:
        """
        Identifies the city or department mentioned in the user's question.
        
        Handles ambiguous cases with a two-step LLM process.

        Args:
            prompt (str): The user's question.

        Returns:
            str: The detected city or department.
        """
        # Check with the llm if the city or department mentioned in the prompt is ambiguous (homonyms, incomplete names, etc.)
        formatted_prompt = prompt_instructions["get_city_prompt"].format(prompt=prompt)
        self.city = self.model.predict(formatted_prompt).strip()

        # If there is no ambiguity, retrieve the city name in a second LLM call
        if self.city=='correct':
            formatted_prompt = prompt_instructions["get_city_prompt_2"].format(prompt=prompt)
            self.city = self.model.predict(formatted_prompt).strip()
        return self.city

    def get_topk(self, prompt: str):
        """
        Identifies if the number of institutions to display is mentioned in the user's question.
        
        Limits the number to a maximum of 50.

        Args:
            prompt (str): The user's question.

        Returns:
            int or str: The number of institutions to display, or 'non mentionné' if not specified or above 50.
        """
        formatted_prompt = prompt_instructions["get_topk_prompt"].format(prompt=prompt)
        topk = self.model.predict(formatted_prompt).strip()
        if topk!='non mentionné':
            if int(topk)>50:
                topk='non mentionné'
            else:
                topk=int(topk)
        return topk

    def get_etablissement_list(self):
        """
        Returns a formatted, deduplicated list of institutions present in the rankings.
        
        Cleans names to avoid duplicates or matching errors.

        Returns:
            str: A comma-separated string of institution names.
        """
        coordonnees_df = pd.read_excel(self.paths["coordonnees_path"])
        colonne_1 = coordonnees_df.iloc[:, 0]
        # Remove location details after commas for better matching
        liste_etablissement = [element.split(",")[0] for element in colonne_1]
        liste_etablissement = list(set(liste_etablissement))
        # Remove generic names that could cause false matches
        liste_etablissement = [element for element in liste_etablissement if element != "CHU"]
        liste_etablissement = [element for element in liste_etablissement if element != "CH"]
        liste_etablissement = ", ".join(map(str, liste_etablissement))
        return liste_etablissement

    def is_public_or_private(self, prompt: str) -> str:
        """
        Determines if the user's question mentions a public or private hospital, or none.
        
        Also detects if a specific institution is mentioned.

        Args:
            prompt (str): The user's question.

        Returns:
            str: The detected institution type or name.
        """

        liste_etablissement=self.get_etablissement_list()

        #On va ensuite appeler notre LLM qui va pouvoir détecter si l'un des établissements est mentionné dans la question de l'utilisateur
        formatted_prompt =prompt_instructions["is_public_or_private_prompt"].format(liste_etablissement=liste_etablissement,prompt=prompt) 
        self.etablissement_name = self.model.predict(formatted_prompt).strip()

  
        if self.etablissement_name in liste_etablissement:
            self.établissement_mentionné = True
            if self.établissement_mentionné:
                self.city='aucune correspondance'
            # Retrieve the category (public/private) of this institution
            coordonnees_df = pd.read_excel(self.paths["coordonnees_path"])
            ligne_saut = coordonnees_df[coordonnees_df['Etablissement'].str.contains(self.etablissement_name,case=False, na=False)]
            self.ispublic = ligne_saut.iloc[0,4]
        else:
            # If no institution is detected, check if a public/private criterion is mentioned
            formatted_prompt = prompt_instructions["is_public_or_private_prompt2"].format(prompt=prompt) 
            ispublic = self.model.predict(formatted_prompt).strip()
            self.établissement_mentionné = False
            self.ispublic = ispublic
        return self.ispublic

    def continuer_conv(self, prompt: str , conv_history: list) -> str:
        """
        Generates a response to the user's new question, taking into account the conversation history.

        Args:
            prompt (str): The user's new question.
            conv_history (list): The conversation history.

        Returns:
            str: The LLM's generated response.
        """

        formatted_prompt = prompt_instructions["continuer_conv_prompt"].format(prompt=prompt,conv_history=conv_history) 
        self.newanswer  = self.model.predict(formatted_prompt).strip()
        return self.newanswer