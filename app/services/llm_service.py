"""
Service for interacting with the language model (LLM).

This file defines the Appels_LLM class, which handles all LLM-based extraction of
    specialties, cities, institution types, and other information from user queries.
"""

import os
from langchain_openai import ChatOpenAI
import pandas as pd
from dotenv import load_dotenv

from app.utils.config import PATHS
from app.utils.prompts import prompt_instructions
from app.utils.specialties import specialties_dict
from app.utils.formatting import format_mapping_words_csv, format_correspondance_list
from app.utils.logging import get_logger
logger = get_logger(__name__)

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
        
        logger.info("Initializing Appels_LLM")
        load_dotenv(override = False) 
        self.model = self.init_model()
        self.palmares_df = None
        self.etablissement_name=None
        self.specialty= None
        self.ispublic= None
        self.city = None
        self.établissement_mentionné = None
        
        # Define the base directory and paths for data files
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.paths= PATHS
        
        self.key_words=format_mapping_words_csv(self.paths["mapping_word_path"])

    def init_model(self) -> ChatOpenAI:
        """
        Initializes and returns the ChatOpenAI model using the API key from environment variables.

        Returns:
            ChatOpenAI: An instance of the ChatOpenAI model.
        """
        
        logger.info("Initializing ChatOpenAI model")
        api_key = os.getenv("OPENAI_API_KEY")
        self.model = ChatOpenAI(
            openai_api_key=api_key,
            model="gpt-4o-mini"
        )
        logger.info("ChatOpenAI model initialized")
        return self.model
    
    def get_specialty_list(self):
        """
        Retrieves the list of medical specialties from the rankings Excel file.

        Returns:
            str: A comma-separated string of all specialties.
        """
        logger.info("Loading specialties from Excel")
        df_specialty = pd.read_excel(self.paths["palmares_path"] , sheet_name="Palmarès")
        self.palmares_df=df_specialty
        colonne_1 = df_specialty.iloc[:, 0].drop_duplicates()
        liste_spe = ", ".join(map(str, colonne_1.dropna()))
        logger.debug(f"Specialty list: {liste_spe}")
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
        logger.info(f"Detecting specialty for prompt: {prompt}")
        liste_spe=self.get_specialty_list()
        #On fait appel au LLM pour déterminer la spécialité concernée
        get_speciality_prompt_formatted=prompt_instructions["get_speciality_prompt"].format(liste_spe=liste_spe,prompt=prompt)
        #self.specialty = self.model.invoke(get_speciality_prompt_formatted).strip()
        logger.debug(f"LLM prompt: {get_speciality_prompt_formatted}")
        response1 = self.model.invoke(get_speciality_prompt_formatted)
        logger.debug(f"LLM response: {response1}")
        if hasattr(response1, "content"):
            self.specialty = response1.content.strip()
        else:
            self.specialty = str(response1).strip()

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
            self.specialty=format_correspondance_list(liste_spe)
            return self.specialty
        else:
            if self.specialty == 'aucune correspondance':
                logger.info("No specialty match, retrying with keyword mapping")
                # Retry with keyword mapping if no match is found
                mapping_words=self.key_words
                second_get_speciality_prompt_formatted=prompt_instructions["second_get_speciality_prompt"].format(prompt=prompt,mapping_words=mapping_words)
                #self.specialty = self.model.invoke(second_get_speciality_prompt_formatted).strip()
                response2 = self.model.invoke(second_get_speciality_prompt_formatted)
                logger.debug(f"LLM response (retry): {response2}")
                if hasattr(response2, "content"):
                    self.specialty = response2.content.strip()
                else:
                    self.specialty = str(response2).strip()
                    
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
        
        logger.info(f"Checking if prompt is deeply off-topic: {prompt}")
        formatted_prompt=prompt_instructions["get_offtopic_approfondi_prompt"].format(prompt=prompt)
        #res = self.model.invoke(formatted_prompt).strip()
        response = self.model.invoke(formatted_prompt)
        if hasattr(response, "content"):
            res = response.content.strip()
        else:
            res = str(response).strip()
        logger.debug(f"LLM response: {response}")
        return res
    
    def get_offtopic(self, prompt: str) -> str:
        """
        Determines if the user's question is off-topic for the assistant.

        Args:
            prompt (str): The user's question.

        Returns:
            str: The LLM's off-topic assessment.
        """
        logger.info(f"Checking if prompt is off-topic: {prompt}"
        formatted_prompt=prompt_instructions["get_offtopic_prompt"].format(prompt=prompt)
        #self.isofftopic = self.model.invoke(formatted_prompt).strip()
        response = self.model.invoke(formatted_prompt)
        if hasattr(response, "content"):
            self.isofftopic = response.content.strip()
        else:
            self.isofftopic = str(response).strip()
        logger.debug(f"LLM response: {response}")
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
        
        logger.info(f"Detecting city in prompt: {prompt}")
        # Check with the llm if the city or department mentioned in the prompt is ambiguous (homonyms, incomplete names, etc.)
        formatted_prompt = prompt_instructions["get_city_prompt"].format(prompt=prompt)
        #self.city = self.model.invoke(formatted_prompt).strip()
        response1 = self.model.invoke(formatted_prompt)
        logger.debug(f"LLM response: {response1}")
        if hasattr(response1, "content"):
            self.city = response1.content.strip()
        else:
            self.city = str(response1).strip()

        # If there is no ambiguity, retrieve the city name in a second LLM call
        if self.city=='correct':
            logger.info("City detected as correct, refining with second LLM call")
            formatted_prompt = prompt_instructions["get_city_prompt_2"].format(prompt=prompt)
            #self.city = self.model.invoke(formatted_prompt).strip()
            response2 = self.model.invoke(formatted_prompt)
            if hasattr(response2, "content"):
                self.city = response2.content.strip()
            else:
                self.city = str(response2).strip()
            logger.debug(f"LLM response (second call): {response2}")
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
        
        logger.info(f"Detecting top_k in prompt: {prompt}")
        formatted_prompt = prompt_instructions["get_topk_prompt"].format(prompt=prompt)
        #topk = self.model.invoke(formatted_prompt).strip()
        response = self.model.invoke(formatted_prompt)
        if hasattr(response, "content"):
            topk = response.content.strip()
        else:
            topk = str(response).strip()
        if topk!='non mentionné':
            if int(topk)>50:
                topk='non mentionné'
            else:
                topk=int(topk)
        logger.debug(f"LLM response: {response}")
        return topk

    def get_etablissement_list(self):
        """
        Returns a formatted, deduplicated list of institutions present in the rankings.
        
        Cleans names to avoid duplicates or matching errors.

        Returns:
            str: A comma-separated string of institution names.
        """
        
        logger.info("Loading institution list from Excel")
        coordonnees_df = pd.read_excel(self.paths["coordonnees_path"])
        colonne_1 = coordonnees_df.iloc[:, 0]
        # Remove location details after commas for better matching
        liste_etablissement = [element.split(",")[0] for element in colonne_1]
        liste_etablissement = list(set(liste_etablissement))
        # Remove generic names that could cause false matches
        liste_etablissement = [element for element in liste_etablissement if element != "CHU"]
        liste_etablissement = [element for element in liste_etablissement if element != "CH"]
        liste_etablissement = ", ".join(map(str, liste_etablissement))
        logger.debug(f"Institution list: {liste_etablissement}")
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

        logger.info(f"Detecting public/private for prompt: {prompt}")
        liste_etablissement=self.get_etablissement_list()

        #On va ensuite appeler notre LLM qui va pouvoir détecter si l'un des établissements est mentionné dans la question de l'utilisateur
        formatted_prompt =prompt_instructions["is_public_or_private_prompt"].format(liste_etablissement=liste_etablissement,prompt=prompt) 
        #self.etablissement_name = self.model.invoke(formatted_prompt).strip()
        response1 = self.model.invoke(formatted_prompt)
        if hasattr(response1, "content"):
            self.etablissement_name = response1.content.strip()
        else:
            self.etablissement_name = str(response1).strip()
        logger.debug(f"LLM response: {response1}")
        
        # If an institution is detected, check if it is in the list of institutions
        if self.etablissement_name in liste_etablissement:
            logger.info(f"Institution mentioned: {self.etablissement_name}")
            self.établissement_mentionné = True
            if self.établissement_mentionné:
                self.city='aucune correspondance'
            # Retrieve the category (public/private) of this institution
            coordonnees_df = pd.read_excel(self.paths["coordonnees_path"])
            ligne_saut = coordonnees_df[coordonnees_df['Etablissement'].str.contains(self.etablissement_name,case=False, na=False)]
            self.ispublic = ligne_saut.iloc[0,4]
        else:
            logger.info("No institution detected, checking for public/private criterion")
            # If no institution is detected, check if a public/private criterion is mentioned
            formatted_prompt = prompt_instructions["is_public_or_private_prompt2"].format(prompt=prompt) 
            #ispublic = self.model.invoke(formatted_prompt).strip()
            response2 = self.model.invoke(formatted_prompt)
            if hasattr(response2, "content"):
                ispublic = response2.content.strip()
            else:
                ispublic = str(response2).strip()
            logger.debug(f"LLM response (second call): {response2}")
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

        logger.info(f"Continuing conversation with prompt: {prompt}")
        logger.debug(f"Conversation history: {conv_history}")
        formatted_prompt = prompt_instructions["continuer_conv_prompt"].format(prompt=prompt,conv_history=conv_history) 
        #self.newanswer  = self.model.invoke(formatted_prompt).strip()
        response = self.model.invoke(formatted_prompt)
        if hasattr(response, "content"):
            self.newanswer = response.content.strip()
        else:
            self.newanswer = str(response).strip()
        logger.debug(f"LLM response: {response}")
        return self.newanswer
