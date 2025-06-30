"""
Main pipeline orchestration for chatbot query processing.

This file defines the Pipeline class, which coordinates the extraction, filtering,
    ranking, and formatting of hospital data in response to user queries.
"""

import pandas as pd
from app.services.processing_service import Processing
from app.utils.formatting import tableau_en_texte
from app.utils.config import PATHS
from app.utils.logging import get_logger
logger = get_logger(__name__)

class Pipeline:
    """
    Orchestrates the pipeline for processing user queries about hospital and clinic rankings.
    
    Handles extraction of query information, data retrieval, filtering, and response formatting.
    """
    
    def __init__(self):
        """
        Initializes the Pipeline class, sets up file paths, and prepares variables for query processing.
        """
        self.ranking_file_path= PATHS["ranking_file_path"]
        self.specialty= None
        self.institution_type= None
        self.city = None
        self.no_city= None # Flag indicating if no city was found in the query
        self.df_gen = None # DF for results 
        self.institution_mentioned=None
        self.institution_name=None
        self.answer=Processing() # Instance of Processing for data extraction and transformation

    def reset_attributes(self):
        """
        Resets pipeline attributes for a new user query.
        """
        logger.debug("Resetting pipeline attributes for new query")
        for attr in [
            "specialty", "institution_type", "city", "df_with_cities", "specialty_df",
            "no_city", "institution_mentioned", "institution_name", "df_gen"
        ]:
            setattr(self, attr, None)

    def get_infos_pipeline(self, prompt: str)->str:
        """
        Retrieves key aspects of the user query: city, institution type, and specialty.
        Updates instance variables accordingly.
        Args:
            prompt (str): The user's question.
        Returns:
            str: The detected specialty.
        """
        logger.info(f"Getting infos from pipeline for prompt: {prompt}")
        self.answer.get_infos(prompt)
        for attr in ["specialty", "city", "institution_type", "institution_mentioned", "institution_name"]:
            setattr(self, attr, getattr(self.answer, attr))
        logger.debug(f"Pipeline infos - specialty: {self.specialty}, city: {self.city}, institution_type: {self.institution_type}, institution: {self.institution_name}")
        return self.specialty

    def from_prompt_to_ranking_df_with_distances(self, prompt: str, excel_path: str )-> pd.DataFrame:
        """
        Retrieves the ranking DataFrame based on the user query, including distance calculations if a city is specified.
        Args:
            prompt (str): The user's question.
            excel_path (str): Path to the ranking Excel file.
        Returns:
            pd.DataFrame: DataFrame with ranking and distance information, or general results if no city is found.
        """
        logger.info(f"Building ranking DataFrame with distances for prompt: {prompt}")
        
        # Find the relevant Excel sheet and extract info
        self.df_gen=self.answer.find_excel_sheet_with_privacy(prompt)
        self.get_infos_pipeline(prompt)
        if self.answer.ranking_not_found:
            logger.warning("Ranking not found for requested specialty/type")
            return self.df_gen
        if self.answer.city == 'aucune correspondance':
            logger.info("No city found in the query, returning general ranking DataFrame")
            self.no_city= True
            return self.df_gen
    
        self.no_city= False
        logger.info("Extracting hospital locations and calculating distances")
        self.answer.extract_local_hospitals()
        return self.answer.get_df_with_distances()
        
    def get_filtered_and_sorted_df(self, df: pd.DataFrame, rayon_max: int, top_k: int, prompt:str) -> str:
        """
        Filters and sorts the ranking DataFrame by distance and score, and formats the response.
        Args:
            df (pd.DataFrame): DataFrame with hospitals and their distances.
            rayon_max (int): Maximum search radius in kilometers.
            top_k (int): Number of top hospitals to return.
            prompt (str): The user's question.
        Returns:
            str: Formatted response string.
        """
        logger.info(f"Filtering and sorting DataFrame with rayon_max={rayon_max}, top_k={top_k}, prompt={prompt}")
        
        # Default value to avoid UnboundLocalError
        reponse = "Aucun résultat trouvé."  
        
        # If an institution was mentioned in user's query, check if it exists in the DataFrame.
        if self.institution_mentioned==True:
            logger.info(f"Institution mentioned in query: {self.institution_name}")
            validity=False
            
            # Check if the institution is present in the DataFrame
            if df['Etablissement'].str.contains(self.institution_name).any():
                validity=True
            
            # If not present, return an appropriate message depending on specialty context
            if validity == False:
                logger.warning(f"Institution {self.institution_name} not found in DataFrame")
                if self.specialty=='aucune correspondance':
                    return f"Cet établissement ne fait pas partie des 50 meilleurs établissements du palmarès global"
                else: 
                    return f"Cet établissement n'est pas présent pour la pathologie {self.specialty}, vous pouvez cependant consulter le classement suivant:"
            
            # If present, find its position in the sorted DataFrame
            df_sorted=df.sort_values(by='Note / 20', ascending=False).reset_index(drop=True)
            position = df_sorted.index[df_sorted["Etablissement"].str.contains(self.institution_name, case=False, na=False)][0] + 1  # +1 for human-readable ranking (starts at 1)
            
            # Build a detailed description of all ranked institutions
            descriptions = []
            for index, row in df_sorted.iterrows():
                description=row[['Etablissement','Catégorie','Note / 20']]

                descriptions.append(str(description))
            response = "<br>\n".join(descriptions)

            #  Build the response string with the institution's rank and context
            response=f"{self.institution_name} est classé n°{position} "
            if self.specialty=='aucune correspondance':
                response=response+f"du palmarès général"
            else:
                response=response+f"du palmarès {self.specialty}."
            if self.institution_type!='aucune correspondance':
                        response=response+f" {self.institution_type}."
            logger.debug(f"Formatted response: {reponse}")
            return response

        # If no specific institution is mentioned, filter hospitals by distance and select the top_k by score
        filtered_df = df[df["Distance"] <= rayon_max]
        self.sorted_df = filtered_df.nlargest(top_k, "Note / 20")
        logger.debug(f"Filtered DataFrame shape: {self.sorted_df.shape}")
        
        if self.sorted_df.shape[0] == top_k:
            logger.info(f"Found {top_k} results within {rayon_max}km")
            # Format the top_k results as a text table
            res_str= tableau_en_texte(self.sorted_df, self.no_city)
            if self.specialty=='aucune correspondance':
                reponse=f"Voici les {top_k} meilleurs établissements du palmarès général dans un rayon de {rayon_max}km autour de {self.city}:\n{res_str}"
            else:
                reponse=f"Voici les {top_k} meilleurs établissements pour la pathologie: {self.specialty} dans un rayon de {rayon_max}km autour de {self.city}:\n{res_str}"
            # Save the query and response to history
            self.answer.create_csv(question=prompt, reponse=reponse)
            logger.debug(f"Formatted response: {reponse}")
            return reponse
        # If the search radius is at its maximum, return all found institutions (even if less than top_k)
        elif rayon_max==500:
            res_str= tableau_en_texte(self.sorted_df, self.no_city)
            if self.specialty=='aucune correspondance':
                reponse=f"Voici les {self.sorted_df.shape[0]} meilleurs établissements au classement général dans un rayon de {rayon_max}km autour de {self.city}:<br>\n{res_str}"
            else:
                reponse=f"Voici les {self.sorted_df.shape[0]} meilleurs établissements pour la pathologie {self.specialty} dans un rayon de {rayon_max}km autour de {self.city}:<br>\n{res_str}"
            self.answer.create_csv(question=prompt, reponse=reponse)
            logger.debug(f"Formatted response: {reponse}")
            return reponse
        
        # If no results found, return None so the caller can try with a larger radius
        logger.warning("No results found within current radius")
        return None

    def final_answer(self, 
        prompt: str, top_k: int = 3, rayon_max: int = 50, specialty_st: str=None) -> str:
        """
        Main entry point: processes the user question and returns a formatted answer with ranking and links.

        Args:
            prompt (str): The user's question.
            top_k (int, optional): Number of top hospitals to return. Defaults to 3.
            rayon_max (int, optional): Search radius in kilometers. Defaults to 50.
            specialty_st (str, optional): Specialty to use if already known.

        Returns:
            str or tuple: The formatted answer and any relevant links.
        """

        logger.info(f"Generating final answer for prompt: {prompt}, top_k={top_k}, rayon_max={rayon_max}, specialty_st={specialty_st}")
        
        # Reset relevant attributes for a new query
        self.reset_attributes()
        self.specialty= specialty_st
        logger.debug("Reset attributes and set specialty for new query")

        # Check if the user specified a different top_k in their prompt
        top_kbis = self.answer.llm_service.detect_topk(prompt)
        if top_kbis!='non mentionné':
            top_k=top_kbis

        # Defensive insertion: ensure specialty_st is never empty or None
        if not specialty_st or (isinstance(specialty_st, str) and specialty_st.strip() == ""):
            specialty_st = "aucune correspondance"
        
        # Set the specialty in the processing service
        if self.specialty is not None:
            self.answer.specialty= specialty_st
        else:
            self.answer.specialty= None
        relevant_file=self.ranking_file_path
        
        # Retrieve the DataFrame with ranking and (if applicable) distances
        df = self.from_prompt_to_ranking_df_with_distances(prompt, relevant_file)
        
        # Handle geolocation API errors
        if self.answer.geopy_problem:
            logger.error("Geopy API error encountered, cannot calculate distances")
            return "Dû à une surutilisation de l'API de Geopy, le service de calcul des distances est indisponible pour le moment, merci de réessayer plus tard ou de recommencer avec une question sans localisation spécifique "

        self.link=self.answer.web_ranking_link

        # Handle cases where no results are found for the requested specialty/type
        if self.answer.ranking_not_found :
            logger.warning("Ranking not found for requested specialty/type, suggesting alternative")
            if self.answer.institution_type=='Public':   
                return "Nous n'avons pas d'établissement publique pour cette pathologie, mais un classement des établissements privés existe. ", self.link
            elif self.answer.institution_type=='Privé': 
                return "Nous n'avons pas d'établissement privé pour cette pathologie, mais un classement des établissements publics existe. ", self.link

        # If a specific institution is mentioned, return its ranking and the link
        if self.institution_mentioned:
            logger.info("Returning result for mentioned institution")
            res=self.get_filtered_and_sorted_df(df, rayon_max, top_k,prompt)
            logger.debug(f"Result: {res}, Links: {self.link}")
            return res, self.link
        
        # If a city was found, try to find results within increasing radii
        if self.no_city== False:
            logger.info("City found, searching for results within increasing radii")
            # Try with initial radius
            res = self.get_filtered_and_sorted_df(df, rayon_max, top_k,prompt)
            if res:
                logger.debug(f"Result: {res}, Links: {self.link}")
                return res, self.link
            # If no result, try with 100km radius
            rayon_max2 = 100
            res = self.get_filtered_and_sorted_df(df, rayon_max2, top_k,prompt)
            if res:
                self.answer.create_csv(question=prompt, reponse=res)
                logger.debug(f"Result: {res}, Links: {self.link}")
                return res, self.link
             # If still no result, try with 200 km
            rayon_max2 = 200
            res = self.get_filtered_and_sorted_df(df, rayon_max2, top_k,prompt)
            if res:
                self.answer.create_csv(question=prompt, reponse=res)
                logger.debug(f"Result: {res}, Links: {self.link}")
                return res, self.link
            # If still no result, try with 500 km (maximum)
            rayon_max3 = 500
            res=self.get_filtered_and_sorted_df(df, rayon_max3, top_k,prompt)
            self.answer.create_csv(question=prompt, reponse=res)
            logger.debug(f"Result: {res}, Links: {self.link}")
            return res, self.link
        
        else:
            logger.info("No city found, returning general ranking")
            # If no city was found, return the top_k institutions from the general ranking 
            self.get_infos_pipeline(prompt)
            res_tab=self.df_gen.nlargest(top_k, "Note / 20")
            res_str = tableau_en_texte(res_tab, self.no_city)
            if top_k==1:
                res=f"Voici le meilleur établissement "
            else: 
                res=f"Voici les {top_k} meilleurs établissements "
            if self.specialty== 'aucune correspondance':
                res=res+f":<br> \n{res_str}"
            else:
                res=res+f"pour la pathologie {self.specialty}<br> \n{res_str}"
            logger.debug(f"Result: {res}, Links: {self.link}")
            return (res, self.link)

